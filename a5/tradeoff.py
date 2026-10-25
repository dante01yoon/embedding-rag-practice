import time

import faiss
import numpy as np

docs = np.load("vectors/docs_ko.npy")  # 위키 문서 32,651개 × 숫자 1024개
queries = np.load("vectors/queries_ko.npy")  # 질문 100개


def measure(index):
    t = time.perf_counter()
    found = [index.search(q[None], 10)[1][0] for q in queries]  # 질문을 하나씩 보낸다
    return found, (time.perf_counter() - t) / len(queries) * 1000


def build(index):
    if not index.is_trained:
        index.train(docs)  # IVF · 양자화는 먼저 학습
    index.add(docs)
    return index


ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(1024), 1024, 256, faiss.METRIC_INNER_PRODUCT)
ivf.nprobe = 8
indexes = {
    "정확 탐색": faiss.IndexFlatIP(1024),
    "IVF 8구역": ivf,
    "HNSW": faiss.IndexHNSWFlat(1024, 32, faiss.METRIC_INNER_PRODUCT),
    "양자화 SQ8": faiss.IndexScalarQuantizer(1024, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT),
    "양자화 PQ64": faiss.IndexPQ(1024, 64, 8, faiss.METRIC_INNER_PRODUCT),
}
print("    시간  재현율    메모리  방법")
for name, index in indexes.items():
    found, ms = measure(build(index))
    if name == "정확 탐색":
        truth = found
    recall = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(found, truth)])
    mb = len(faiss.serialize_index(index)) / 1e6  # 색인을 파일로 쓰면 몇 MB인가
    print(f"{ms:6.2f}ms {recall:6.2f} {mb:7.1f}MB  {name}")
