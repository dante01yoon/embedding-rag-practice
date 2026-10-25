import json
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], d["title"], c) for d in docs for c in split(d["text"], 500, 100)]
qa = json.load(open("k8s/qa_ko_reviewed.json"))
model = SentenceTransformer("BAAI/bge-m3")
vecs = np.load("k8s/vecs_ko_500.npy")
vecs_title = model.encode([f"문서: {t}\n{c}" for _, t, c in chunks], normalize_embeddings=True, batch_size=16)  # 제목을 앞에 붙여 다시 임베딩

for name, V in [("그대로", vecs), ("제목 붙임", vecs_title)]:
    hits, rr = [], []
    for item in qa:
        q = model.encode(item["question"], normalize_embeddings=True)
        paths = [chunks[i][0] for i in np.argsort(-(V @ q))[:10]]
        hit = next((r + 1 for r, p in enumerate(paths) if p == item["path"]), None)
        hits.append(hit is not None and hit <= 4)
        rr.append(1 / hit if hit else 0)
    print(f"{name:6s} Recall@4 {np.mean(hits):.2f} · MRR@10 {np.mean(rr):.2f}")
