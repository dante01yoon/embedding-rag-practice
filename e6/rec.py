import csv
import random

import numpy as np

books = list(csv.DictReader(open("books/books_clean.csv")))
vecs = np.load("books/vecs_desc.npy")  # 사례의 '배치 임베딩': 미리 만들어 둔 책 벡터
GENRES = ["SF", "판타지", "추리 소설", "논픽션", "역사소설", "범죄물"]
by = {g: [i for i, b in enumerate(books) if b["genre"] == g] for g in GENRES}
stock = {i for i, b in enumerate(books) if int(b["pageid"]) % 20 == 0}  # 지금 빌릴 수 있는 책 (배달 가능 가게처럼 조건)
rng = random.Random(0)
sessions = []  # 오래된 취향 5권(장르 A) + 방금 누른 2권(장르 B) → 다음에 누를 1권(장르 B)
for _ in range(200):
    a, b = rng.sample(GENRES, 2)
    old, new = rng.sample(by[a], 5), rng.sample(by[b], 3)
    sessions.append((old, new[:2], new[2]))


def unit(v):
    return v / np.linalg.norm(v)


def recommend(old, recent, w, k=10, pool=None):  # w = 방금 누른 것의 비중 (0이면 오래된 취향만)
    q = unit((1 - w) * unit(vecs[old].mean(0)) + w * unit(vecs[recent].mean(0)))
    s = vecs @ q
    s[old + recent] = -9  # 이미 본 책은 빼기
    if pool is not None:  # 사전 필터: 조건에 맞는 책 안에서만 순위를 매긴다
        s[[i for i in range(len(books)) if i not in pool]] = -9
    return list(np.argsort(-s)[:k])


for w in [0.0, 0.5, 0.8]:
    hit = np.mean([nxt in recommend(old, recent, w) for old, recent, nxt in sessions])
    print(f"방금 누른 것 비중 {w:.1f} | 다음 클릭 Hit@10 {hit * 100:4.1f}%")


def post_filter(old, recent, w=0.8, n=50):  # 사후 필터: 가까운 n권을 먼저 뽑고 재고만 남긴다
    return [i for i in recommend(old, recent, w, k=n) if i in stock][:10]


got = [post_filter(old, recent) for old, recent, _ in sessions]
print(f"사후 필터 | 추천 0권인 세션 {sum(not g for g in got)}/{len(got)} · 평균 {np.mean([len(g) for g in got]):.1f}권")
got = [recommend(old, recent, 0.8, pool=stock) for old, recent, _ in sessions]
print(f"사전 필터 | 추천 0권인 세션 {sum(not g for g in got)}/{len(got)} · 평균 {np.mean([len(g) for g in got]):.1f}권")
