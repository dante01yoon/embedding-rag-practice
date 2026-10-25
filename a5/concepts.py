"""개념 장면에 쓰는 실측값: 정확 탐색 비용 · IVF 구역 크기 · HNSW 설정값 · 양자화 메모리."""
import time

import faiss
import numpy as np

docs = np.load("vectors/docs_ko.npy")
queries = np.load("vectors/queries_ko.npy")


def search(index, k=10):
    t = time.perf_counter()
    _, ids = index.search(queries, k)
    return ids, (time.perf_counter() - t) / len(queries) * 1000


def one_by_one(index, reps=5):  # 질문을 하나씩 보낼 때 (실제 서비스처럼) · 5번 재서 가운데 값
    out = []
    for _ in range(reps):
        t = time.perf_counter()
        for q in queries:
            index.search(q[None], 10)
        out.append((time.perf_counter() - t) / len(queries) * 1000)
    return float(np.median(out))


exact = faiss.IndexFlatIP(1024)
exact.add(docs)
truth, _ = search(exact)


def recall(ids):
    return np.mean([len(set(a) & set(b)) / 10 for a, b in zip(ids, truth)])


def mb(index):
    return len(faiss.serialize_index(index)) / 1e6


print("== 정확 탐색: 문서 수에 따른 시간 (질문 하나씩)")
for n in (4000, 8000, 16000, 32651):
    ix = faiss.IndexFlatIP(1024)
    ix.add(docs[:n])
    print(f"{n:6d}개  {one_by_one(ix):.3f} ms")
print(f"Flat 메모리 {mb(exact):.1f} MB")

print("== IVF")
t = time.perf_counter()
ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(1024), 1024, 256, faiss.METRIC_INNER_PRODUCT)
ivf.train(docs)
tt = time.perf_counter() - t
ivf.add(docs)
sz = [ivf.invlists.list_size(i) for i in range(256)]
print(f"train {tt:.2f}s  구역 크기 min {min(sz)} 평균 {np.mean(sz):.0f} max {max(sz)}  메모리 {mb(ivf):.1f} MB")
for p in (1, 8, 32, 64):
    ivf.nprobe = p
    ids, ms = search(ivf)
    print(f"nprobe {p:2d}  {one_by_one(ivf):.3f} ms(하나씩)  {ms:.3f} ms(묶음)  재현율 {recall(ids):.2f}")

print("== HNSW")
for m in (8, 32):
    t = time.perf_counter()
    h = faiss.IndexHNSWFlat(1024, m, faiss.METRIC_INNER_PRODUCT)
    h.add(docs)
    bt = time.perf_counter() - t
    print(f"M={m} 만들기 {bt:.1f}s 메모리 {mb(h):.1f} MB 층 {h.hnsw.max_level + 1}개")
    for ef in (16, 64, 128):
        h.hnsw.efSearch = ef
        ids, ms = search(h)
        print(f"  efSearch {ef:3d}  {one_by_one(h):.3f} ms(하나씩)  {ms:.3f} ms(묶음)  재현율 {recall(ids):.2f}")
lv = np.bincount(faiss.vector_to_array(h.hnsw.levels) - 1)
print("층별 문서 수(아래→위)", lv.tolist())

print("== 양자화")
sq = faiss.IndexScalarQuantizer(1024, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT)
sq.train(docs)
sq.add(docs)
ids, ms = search(sq)
print(f"SQ8  메모리 {mb(sq):.1f} MB  {one_by_one(sq):.3f} ms  재현율 {recall(ids):.2f}")
pq = faiss.IndexPQ(1024, 64, 8, faiss.METRIC_INNER_PRODUCT)
t = time.perf_counter()
pq.train(docs)
pq.add(docs)
ids, ms = search(pq)
print(f"PQ64 메모리 {mb(pq):.1f} MB  만들기 {time.perf_counter() - t:.1f}s  {one_by_one(pq):.3f} ms  재현율 {recall(ids):.2f}")
