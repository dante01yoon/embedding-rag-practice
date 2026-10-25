import json
import os
import sys

import bm25s
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

model = SentenceTransformer("BAAI/bge-m3")


def score(ranked_paths, gold):  # 문서 단위: 상위 4개 안에 정답 문서가 있나 · 첫 정답 순위의 역수
    hit = next((r + 1 for r, p in enumerate(ranked_paths[:10]) if p == gold), None)
    return (hit is not None and hit <= 4), (1 / hit if hit else 0.0)


for lang in ["ko", "en"]:
    docs = json.load(open(f"k8s/docs_{lang}.json"))
    chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
    qa = json.load(open(f"k8s/qa_{lang}_reviewed.json"))
    # 1) BM25: 띄어쓰기로 자른 단어가 겹치는 정도
    bm = bm25s.BM25()
    bm.index([c.lower().split() for _, c in chunks], show_progress=False)
    # 2) bge-m3: 뜻이 가까운 정도 (벡터는 한 번만 만들어 저장)
    path = f"k8s/vecs_{lang}_500.npy"
    if not os.path.exists(path):
        np.save(path, model.encode([c for _, c in chunks], normalize_embeddings=True, batch_size=16))
    vecs = np.load(path)
    for name in ["BM25", "bge-m3"]:
        hits, rr = [], []
        for item in qa:
            if name == "BM25":
                idx, _ = bm.retrieve([item["question"].lower().split()], k=10, show_progress=False)
                top = idx[0]
            else:
                top = np.argsort(-(vecs @ model.encode(item["question"], normalize_embeddings=True)))[:10]
            h, r = score([chunks[i][0] for i in top], item["path"])
            hits.append(h)
            rr.append(r)
        print(f"{lang}  {name:6s}  질문 {len(qa)}개 · Recall@4 {np.mean(hits):.2f} · MRR@10 {np.mean(rr):.2f}")
