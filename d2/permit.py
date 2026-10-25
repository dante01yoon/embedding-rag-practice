import json
import os
import random
import re
import sys

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_d2.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


docs = json.load(open("k8s/docs_ko.json"))
random.seed(1)
SERVERS = ["알파", "베타", "감마", "델타", "엡실론", "제타", "에타", "세타", "요타", "카파", "람다", "뮤"]
secrets = {s: f"[운영팀 전용] {s} 서버의 점검 암호는 {random.randint(1000, 9999)}이다." for s in SERVERS}
items = [(c, "모두") for d in docs for c in split(d["text"], 500, 100)] + [(t, "운영팀") for t in secrets.values()]  # (청크, 볼 수 있는 사람)
model = SentenceTransformer("BAAI/bge-m3")
vecs = np.vstack([np.load("k8s/vecs_ko_500.npy"), model.encode(list(secrets.values()), normalize_embeddings=True)])
PROMPT = "아래 자료에 나온 내용만으로 답하세요. 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
ANSWERS = {}  # 답 캐시 (질문, 팀)마다 따로


def answer(q, team):
    if (q, team) in ANSWERS:
        return ANSWERS[(q, team)]
    ok = np.array([who in ("모두", team) for _, who in items])  # 권한 필터: 볼 수 있는 청크만 검색
    scores = np.where(ok, vecs @ model.encode(q, normalize_embeddings=True), -1)
    ctx = "\n\n".join(items[i][0] for i in np.argsort(-scores)[:4])
    ANSWERS[(q, team)] = ask(PROMPT.format(ctx=ctx, q=q))
    return ANSWERS[(q, team)]


def leaked(s, a):  # 답에 그 서버의 암호 숫자가 들어 있나
    return re.search(r"\d{4}", secrets[s]).group() in a


ops = sum(leaked(s, answer(f"{s} 서버의 점검 암호는?", "운영팀")) for s in SERVERS)
intern = sum(leaked(s, answer(f"{s} 서버의 점검 암호는?", "인턴")) for s in SERVERS)
print(f"운영팀이 먼저 묻고 → 인턴이 같은 질문 | 운영팀 맞힘 {ops}/12 · 인턴에게 새어 나감 {intern}/12")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
