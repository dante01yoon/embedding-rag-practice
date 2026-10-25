import json
import os
import sys

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
qa = json.load(open("k8s/qa_ko_reviewed.json"))
vecs = np.load("k8s/vecs_ko_500.npy")
model = SentenceTransformer("BAAI/bge-m3")
CACHE = "k8s/llm_cache.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):  # 같은 질문은 저장해 둔 답을 쓴다 → 다시 돌려도 같은 점수
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


def vsearch(text):  # 벡터로 상위 20개
    return np.argsort(-(vecs @ model.encode(text, normalize_embeddings=True)))[:20]


def rrf(*rankings, k=60):
    score = {}
    for ranking in rankings:
        for r, i in enumerate(ranking):
            score[i] = score.get(i, 0) + 1 / (k + r + 1)
    return sorted(score, key=score.get, reverse=True)


def multi(q):  # 질문을 다른 말로 3개 더 쓰고, 넷의 검색 결과를 RRF로 합친다
    alts = ask(f"다음 질문을 같은 뜻의 다른 표현으로 3개 써 주세요. 한 줄에 하나씩, 질문만.\n\n{q}").splitlines()
    return rrf(*[vsearch(x) for x in [q] + alts])


def hyde(q):  # 가상의 답을 먼저 쓰고, 그 답으로 검색한다
    fake = ask(f"다음 질문에 쿠버네티스 문서처럼 짧은 한 문단으로 답해 주세요.\n\n{q}")
    return vsearch(fake)


rows = {}
for item in qa:
    q = item["question"]
    for name, top in [("그대로", vsearch(q)), ("여러 질문", multi(q)), ("가상의 답", hyde(q))]:
        paths = [chunks[i][0] for i in top[:10]]
        hit = next((r + 1 for r, p in enumerate(paths) if p == item["path"]), None)
        rows.setdefault(name, []).append((hit is not None and hit <= 4, 1 / hit if hit else 0))
for name, s in rows.items():
    print(f"{name:8s} Recall@4 {np.mean([a for a, _ in s]):.2f} · MRR@10 {np.mean([b for _, b in s]):.2f}")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
