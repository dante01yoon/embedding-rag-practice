import json

import numpy as np
from sentence_transformers import SentenceTransformer

from chunk import split

docs = json.load(open("k8s/docs_ko.json"))
chunks = [{"title": d["title"], "path": d["path"], "text": c} for d in docs for c in split(d["text"], 500, 100)]
vecs = SentenceTransformer("BAAI/bge-m3").encode([c["text"] for c in chunks], normalize_embeddings=True, batch_size=16)
np.save("k8s/index.npy", vecs)  # 청크 벡터
json.dump(chunks, open("k8s/chunks.json", "w"), ensure_ascii=False)  # 청크 글 + 출처
print("색인 완료", vecs.shape)
