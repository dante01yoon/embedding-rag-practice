import json
import os
import random
import re
import sys
import time
import uuid

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_d2.json"  # 권한 수업과 같은 질문은 저장해 둔 답을 쓴다
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
items = [(c, "모두") for d in docs for c in split(d["text"], 500, 100)] + [(t, "운영팀") for t in secrets.values()]
model = SentenceTransformer("BAAI/bge-m3")
vecs = np.vstack([np.load("k8s/vecs_ko_500.npy"), model.encode(list(secrets.values()), normalize_embeddings=True)])
PROMPT = "아래 자료에 나온 내용만으로 답하세요. 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
LOG = "d5/trace.jsonl"


def answer(q, team):  # 한 번의 요청 = 트레이스 하나 · 단계마다 시간과 결과를 남긴다
    trace = {"id": uuid.uuid4().hex[:8], "team": team, "q": q}
    t = time.time()
    ok = np.array([who in ("모두", team) for _, who in items])
    scores = np.where(ok, vecs @ model.encode(q, normalize_embeddings=True), -1)
    top = np.argsort(-scores)[:4]
    trace["search"] = {"sec": round(time.time() - t, 3), "top": [int(i) for i in top], "score": round(float(scores[top[0]]), 3)}
    t = time.time()
    a = ask(PROMPT.format(ctx="\n\n".join(items[i][0] for i in top), q=q))
    trace["llm"] = {"sec": round(time.time() - t, 3), "answer": re.sub(r"\d{4}", "****", a)}  # 로그에는 네 자리 숫자를 가린다
    with open(LOG, "a") as f:
        f.write(json.dumps(trace, ensure_ascii=False) + "\n")
    return a


open(LOG, "w").close()
QA = [x["question"] for x in json.load(open("k8s/qa_ko_short.json"))]
for q in QA:
    answer(q, "인턴")
for s in SERVERS:
    answer(f"{s} 서버의 점검 암호는?", "운영팀")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)

logs = [json.loads(line) for line in open(LOG)]
no = [x for x in logs if "자료에 없습니다" in x["llm"]["answer"]]
yes = [x for x in logs if x not in no]
print(f"트레이스 {len(logs)}개 · 거절 {len(no)}개 1위 점수 평균 {np.mean([x['search']['score'] for x in no]):.2f} · 답한 것 {np.mean([x['search']['score'] for x in yes]):.2f}")
text = open(LOG).read()
found = sum(re.search(r"\d{4}", v).group() in text for v in secrets.values())  # 진짜 암호 숫자가 로그에 있나
print(f"로그 속 암호 | {found}/12")
