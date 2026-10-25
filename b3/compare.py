import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer

from chunk import split

docs = json.load(open("k8s/docs_ko.json"))
model = SentenceTransformer("BAAI/bge-m3")
QUESTION = "디플로이먼트를 이전 버전으로 되돌리려면 어떻게 하나요?"
ANSWER = "rollout undo"  # 문서에 실제로 있는 정답 명령
q = model.encode(QUESTION, normalize_embeddings=True)

for size, overlap in [(200, 0), (500, 100), (1500, 300)]:
    chunks = [c for d in docs for c in split(d["text"], size, overlap)]
    path = f"k8s/vecs_{size}.npy"
    if not os.path.exists(path):  # 크기마다 한 번만 벡터로 바꿔 저장해 둔다
        np.save(path, model.encode(chunks, normalize_embeddings=True, batch_size=16))
    order = np.argsort(-(np.load(path) @ q))
    rank = next(r + 1 for r, i in enumerate(order) if ANSWER in chunks[i])
    print(f"크기 {size:4d}: 청크 {len(chunks):4d}개 · 정답 명령이 든 청크 {rank}위", "← RAG에 들어감" if rank <= 4 else "")
