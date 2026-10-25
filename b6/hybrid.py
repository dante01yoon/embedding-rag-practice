import json
import sys

import bm25s
import numpy as np
from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
sys.path.insert(0, "b5")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
qa = json.load(open("k8s/qa_ko_reviewed.json"))
vecs = np.load("k8s/vecs_ko_500.npy")  # 지난 섹션에 만든 청크 벡터
model = SentenceTransformer("BAAI/bge-m3")
kiwi = Kiwi()


def words(text):  # 형태소 분석: "파드를" → "파드" + "를", 뜻 있는 말만 남긴다
    return [t.form.lower() for t in kiwi.tokenize(text) if t.tag[0] in "NVS"]


space = bm25s.BM25()
space.index([c.lower().split() for _, c in chunks], show_progress=False)
morph = bm25s.BM25()
morph.index([words(c) for _, c in chunks], show_progress=False)


def rrf(*rankings, k=60):  # 순위 합치기: 각 목록에서 1/(k + 순위)를 더한다
    score = {}
    for ranking in rankings:
        for r, i in enumerate(ranking):
            score[i] = score.get(i, 0) + 1 / (k + r + 1)
    return sorted(score, key=score.get, reverse=True)


def search(q):
    a = space.retrieve([q.lower().split()], k=20, show_progress=False)[0][0]
    b = morph.retrieve([words(q)], k=20, show_progress=False)[0][0]
    v = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:20]
    return {"BM25 띄어쓰기": a, "BM25 형태소": b, "bge-m3": v, "하이브리드(형태소+벡터)": rrf(b, v)}


rows = {}
for item in qa:
    for name, top in search(item["question"]).items():
        paths = [chunks[i][0] for i in top[:10]]
        hit = next((r + 1 for r, p in enumerate(paths) if p == item["path"]), None)
        rows.setdefault(name, []).append((hit is not None and hit <= 4, 1 / hit if hit else 0))
for name, s in rows.items():
    print(f"{name:14s} Recall@4 {np.mean([x[0] for x in s]):.2f} · MRR@10 {np.mean([x[1] for x in s]):.2f}")
