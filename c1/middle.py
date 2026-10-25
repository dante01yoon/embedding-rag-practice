import json
import os
import random
import re
import sys
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_c1.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):  # 답과 입력 토큰을 함께 저장
    if prompt not in cache:
        t = time.time()
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = [r.choices[0].message.content, r.usage.prompt_tokens, time.time() - t]
    return cache[prompt]


docs = json.load(open("k8s/docs_ko.json"))
pool = [c for d in docs for c in split(d["text"], 500, 100)]
random.seed(1)
N = 80
filler = random.sample(pool, N)  # 쿠버네티스 문서 청크 80개
SERVERS = ["알파", "베타", "감마", "델타", "엡실론", "제타", "에타", "세타", "요타", "카파", "람다", "뮤"]
notes = {s: f"[사내 공지] {s} 서버의 점검 암호는 {random.randint(1000, 9999)}이다." for s in SERVERS}  # 모델이 외웠을 리 없는 가짜 사실


def check(ctx, s):  # 자료 ctx를 주고 물어서 맞혔는지, 입력 토큰
    p = "아래 자료를 보고 질문에 숫자 하나로만 답하세요.\n\n" + "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(ctx)) + f"\n\n질문: {s} 서버의 점검 암호는?"
    answer, tokens, sec = ask(p)
    return re.search(r"\d{4}", notes[s]).group() in answer, tokens, sec


print("1) 긴 자료에 통째로 · 공지 위치별")
for pos in [0, N // 4, N // 2, 3 * N // 4, N]:
    res = [check(filler[:pos] + [notes[s]] + filler[pos:], s) for s in SERVERS]
    print(f"  {pos:2d}번째 자리 | 맞힘 {sum(r[0] for r in res)}/12 · 입력 {np.mean([r[1] for r in res]):,.0f}토큰")

model = SentenceTransformer("BAAI/bge-m3")
index = filler + list(notes.values())  # 검색할 청크들 (새 공지도 색인에 넣는다)
vecs = model.encode(index, normalize_embeddings=True)
res = []
for s in SERVERS:
    top = np.argsort(-(vecs @ model.encode(f"{s} 서버의 점검 암호는?", normalize_embeddings=True)))[:4]
    res.append(check([index[i] for i in top], s))
print(f"2) 검색해서 4개만 | 맞힘 {sum(r[0] for r in res)}/12 · 입력 {np.mean([r[1] for r in res]):,.0f}토큰")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
