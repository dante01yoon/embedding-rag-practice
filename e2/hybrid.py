import csv
import json

import bm25s
import numpy as np
from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer

books = list(csv.DictReader(open("books/books_mood.csv")))
qs = json.load(open("books/queries_e2.json"))  # 오타 60개 + 묘사형 60개
ids = [b["pageid"] for b in books]
kiwi = Kiwi()
model = SentenceTransformer("BAAI/bge-m3")


def words(t):
    return [x.form.lower() for x in kiwi.tokenize(t) if x.tag[0] in "NVS"]


bm = bm25s.BM25()  # 어휘 색인: 제목과 작가 이름만 (음악 앱의 곡명·가수 색인처럼)
bm.index([words(f'{b["title"]} {b["author"]}') for b in books], show_progress=False)
vecs = model.encode([f'{b["title"]} / {b["author"]} / {b["genre"]} / {b["description"][:200]}' for b in books], normalize_embeddings=True, batch_size=32)


def lexical(q):  # 책마다 BM25 점수 (겹치는 낱말이 없으면 0)
    s = np.zeros(len(books))
    toks = words(q)
    if toks:
        r, sc = bm.retrieve([toks], k=len(books), show_progress=False)
        s[r[0]] = sc[0]
    return s


rng = np.random.default_rng(0)  # 보정용 가짜 질문 200개: 책 소개의 첫 문장 (평가 질문과 겹치지 않게)
cal = [b["description"].split(".")[0][:80] for b in rng.choice(books, 200, replace=False)]
LX = np.sort(np.concatenate([np.sort(lexical(q))[-50:] for q in cal]))  # 질문마다 위 50개 점수를 모은 분포
VC = np.sort(np.concatenate([np.sort(vecs @ model.encode(q, normalize_embeddings=True))[-50:] for q in cal]))


def quantile(s, dist):  # 점수 → 그 점수가 평소 분포에서 몇 분위인지 (0~1)
    return np.searchsorted(dist, s) / len(dist)


def hybrid(lx, vc, w=0.5):  # 같은 눈금으로 바꾼 뒤 가중 합
    return w * quantile(lx, LX) + (1 - w) * quantile(vc, VC)


res = {}
for x in qs:
    lx, vc = lexical(x["q"]), vecs @ model.encode(x["q"], normalize_embeddings=True)
    gold = ids.index(x["id"])
    for name, s, empty in [("어휘", lx, lx.max() == 0), ("벡터", vc, False), ("하이브리드", hybrid(lx, vc), False)]:
        hit = gold in np.argsort(-s)[:10] and s[gold] > 0
        res.setdefault((name, x["kind"]), []).append((hit, empty))
for name in ["어휘", "벡터", "하이브리드"]:
    a, b = res[(name, "오타")], res[(name, "묘사")]
    print(f"{name:<5} | 오타 Hit@10 {np.mean([h for h, _ in a]) * 100:4.1f}% · 묘사 Hit@10 {np.mean([h for h, _ in b]) * 100:4.1f}% · 빈 결과 {np.mean([e for _, e in a + b]) * 100:4.1f}%")
