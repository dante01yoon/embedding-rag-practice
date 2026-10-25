import json

import numpy as np
from sentence_transformers import SentenceTransformer

chunks = json.load(open("k8s/chunks.json"))  # 색인해 둔 청크 3,033개
vecs = np.load("k8s/index.npy")
model = SentenceTransformer("BAAI/bge-m3")
q = model.encode("디플로이먼트를 이전 버전으로 되돌리려면 어떻게 하나요?", normalize_embeddings=True)
scores = vecs @ q
order = np.argsort(-scores)
for r, i in enumerate(order[:4]):  # RAG가 LLM에게 건넨 청크 4개
    print(r + 1, round(float(scores[i]), 3), chunks[i]["title"], "|", chunks[i]["text"][:40].replace("\n", " "))

ranks = [r + 1 for r, i in enumerate(order) if "rollout undo" in chunks[i]["text"]]
print("정답 명령이 든 청크 순위", ranks[:3], "· 점수", round(float(scores[order[ranks[0] - 1]]), 3))
