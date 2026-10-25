import json
import math

import numpy as np


def precision(ranked, rel, k):  # 상위 k개 중 정답 비율
    return sum(d in rel for d in ranked[:k]) / k


def recall(ranked, rel, k):  # 정답 중 상위 k개 안에 든 비율
    return sum(d in rel for d in ranked[:k]) / len(rel)


ranked, rel = ["가", "나", "다", "라", "마"], {"나", "라", "자"}
print("P@5", precision(ranked, rel, 5), " R@5", round(recall(ranked, rel, 5), 2))


def mrr(ranked, rel, k):  # 첫 정답 등수의 역수
    return next((1 / (i + 1) for i, d in enumerate(ranked[:k]) if d in rel), 0.0)


print("MRR", mrr(ranked, rel, 5))


def ndcg(ranked, rel, k):  # 아래로 갈수록 깎은 점수 ÷ 가장 좋은 순서의 점수
    dcg = sum(1 / math.log2(i + 2) for i, d in enumerate(ranked[:k]) if d in rel)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(len(rel), k)))
    return dcg / ideal


print("nDCG", round(ndcg(ranked, rel, 5), 2))

# 정답 하나가 1등에서 5등까지 내려가면
for pos in range(5):
    five = ["오답"] * 5
    five[pos] = "정답"
    m = [round(f(five, {"정답"}, 5), 2) for f in (precision, recall, mrr, ndcg)]
    print(f"{pos + 1}등", "P R MRR nDCG =", m)

# 실제 위키 질문 100개 · bge-m3 검색 결과 상위 10개
docs, qv = np.load("vectors/docs_ko.npy"), np.load("vectors/queries_ko.npy")
ids = json.load(open("vectors/docids_ko.json"))
qids = [line.split("\t")[0] for line in open("vectors/queries_ko.tsv")]
rels = {}
for line in open("vectors/qrels_ko.tsv"):
    q, d, r = line.split()
    if int(r) > 0:
        rels.setdefault(q, set()).add(d)
top = np.argsort(-(qv @ docs.T), axis=1)[:, :10]
runs = [([ids[j] for j in row], rels[q]) for q, row in zip(qids, top)]
for k in (1, 3, 5, 10):
    s = {f.__name__: np.mean([f(r, g, k) for r, g in runs]) for f in (precision, recall, mrr, ndcg)}
    print(f"k={k:<2}", {n: round(float(v), 2) for n, v in s.items()})
