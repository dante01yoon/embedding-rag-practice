import json
import sys
import time

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
qa = json.load(open("k8s/qa_ko_reviewed.json"))
vecs = np.load("k8s/vecs_ko_500.npy")
embed = SentenceTransformer("BAAI/bge-m3")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")  # 질문과 청크를 한 쌍으로 같이 읽고 점수를 매긴다


def evaluate(name, ranked_lists):
    hits, rr = [], []
    for item, top in zip(qa, ranked_lists):
        paths = [chunks[i][0] for i in top[:10]]
        hit = next((r + 1 for r, p in enumerate(paths) if p == item["path"]), None)
        hits.append(hit is not None and hit <= 4)
        rr.append(1 / hit if hit else 0)
    print(f"{name:16s} Recall@4 {np.mean(hits):.2f} · MRR@10 {np.mean(rr):.2f}")


first = [np.argsort(-(vecs @ embed.encode(item["question"], normalize_embeddings=True)))[:20] for item in qa]  # 1단계: 벡터로 20개
evaluate("bge-m3", first)

start = time.time()
second = []
for item, top in zip(qa, first):  # 2단계: 20개만 재정렬 모델로 다시 점수
    scores = reranker.predict([(item["question"], chunks[i][1]) for i in top])
    second.append([top[j] for j in np.argsort(-scores)])
evaluate("bge-m3 + 재정렬", second)
print(f"재정렬 시간: 질문 하나당 {(time.time() - start) / len(qa):.2f}초 (청크 20개)")
