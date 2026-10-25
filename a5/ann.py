import time

import faiss
import numpy as np

docs = np.load("vectors/docs_ko.npy")  # 위키 문서 32,651개 × 숫자 1024개 (bge-m3)
queries = np.load("vectors/queries_ko.npy")  # 질문 100개
print(docs.shape, queries.shape)


def search(index):
    t = time.perf_counter()
    ids = [index.search(q[None], 10)[1][0] for q in queries]  # 질문을 하나씩 보내 가까운 문서 10개
    return ids, (time.perf_counter() - t) / len(queries) * 1000  # 질문 하나에 걸린 ms


def recall(ids):
    return np.mean([len(set(a) & set(b)) / 10 for a, b in zip(ids, truth)])  # 정확 탐색 10개 중 몇 개를 찾았나


exact = faiss.IndexFlatIP(1024)  # 정확 탐색: 전부와 하나씩 비교
exact.add(docs)
truth, ms = search(exact)
print(f"정확 탐색   {ms:5.2f} ms   재현율 1.00")

ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(1024), 1024, 256, faiss.METRIC_INNER_PRODUCT)  # IVF: 구역 256개
ivf.train(docs)  # 문서를 보고 구역 중심 256개 정하기
ivf.add(docs)
for nprobe in (1, 8, 32):
    ivf.nprobe = nprobe  # 가까운 구역 몇 개를 뒤질지
    ids, ms = search(ivf)
    print(f"IVF {nprobe:2d}구역  {ms:5.2f} ms   재현율 {recall(ids):.2f}")

hnsw = faiss.IndexHNSWFlat(1024, 32, faiss.METRIC_INNER_PRODUCT)  # HNSW: 문서마다 이웃 32개
hnsw.add(docs)
ids, ms = search(hnsw)
print(f"HNSW        {ms:5.2f} ms   재현율 {recall(ids):.2f}")
