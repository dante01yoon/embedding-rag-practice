import json
import os
import sys

import bm25s
import numpy as np
from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
qa = json.load(open("k8s/qa_ko_reviewed.json"))
ctx = json.load(open("k8s/ctx_ko.json"))  # contextualize.py로 미리 만든 청크별 맥락 한두 문장
texts = [ctx[str(i)] + "\n" + c for i, (_, c) in enumerate(chunks)]  # 맥락을 청크 앞에 붙인다
model = SentenceTransformer("BAAI/bge-m3")
kiwi = Kiwi()

vecs = np.load("k8s/vecs_ko_500.npy")
if not os.path.exists("k8s/vecs_ko_ctx.npy"):
    np.save("k8s/vecs_ko_ctx.npy", model.encode(texts, normalize_embeddings=True, batch_size=16))
vecs_ctx = np.load("k8s/vecs_ko_ctx.npy")


def words(text):
    return [t.form.lower() for t in kiwi.tokenize(text) if t.tag[0] in "NVS"]


bm = bm25s.BM25()
bm.index([words(c) for _, c in chunks], show_progress=False)
bm_ctx = bm25s.BM25()
bm_ctx.index([words(t) for t in texts], show_progress=False)


def rrf(*rankings, k=60):
    score = {}
    for ranking in rankings:
        for r, i in enumerate(ranking):
            score[i] = score.get(i, 0) + 1 / (k + r + 1)
    return sorted(score, key=score.get, reverse=True)


rows = {}
for item in qa:
    qv = model.encode(item["question"], normalize_embeddings=True)
    v, vc = np.argsort(-(vecs @ qv))[:20], np.argsort(-(vecs_ctx @ qv))[:20]
    b = bm.retrieve([words(item["question"])], k=20, show_progress=False)[0][0]
    bc = bm_ctx.retrieve([words(item["question"])], k=20, show_progress=False)[0][0]
    for name, top in [("벡터", v), ("벡터 + 맥락", vc), ("BM25", b), ("BM25 + 맥락", bc), ("하이브리드", rrf(b, v)), ("하이브리드 + 맥락", rrf(bc, vc))]:
        paths = [chunks[i][0] for i in top[:10]]
        hit = next((r + 1 for r, p in enumerate(paths) if p == item["path"]), None)
        rows.setdefault(name, []).append((hit is not None and hit <= 4, 1 / hit if hit else 0, hit is not None and hit <= 10))
for name, s in rows.items():
    print(f"{name:12s} Recall@4 {np.mean([a for a, _, _ in s]):.2f} · MRR@10 {np.mean([b for _, b, _ in s]):.2f} · 10위 안 실패 {sum(not c for _, _, c in s)}개")
