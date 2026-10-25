import json
import math
import sys

import bm25s
from kiwipiepy import Kiwi

D = "a4/miracl_ko/"
docs = [json.loads(x) for x in open(D + "corpus.jsonl")]  # 위키백과 문단
queries = [x.rstrip("\n").split("\t") for x in open(D + "queries.tsv")]  # 질문 100개
gold = {}  # 질문마다 사람이 표시한 정답 문단
for x in open(D + "qrels.tsv"):
    q, d, r = x.split()
    gold.setdefault(q, {})[d] = int(r)
k1 = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
kiwi = Kiwi()
KEEP = ("NN", "VV", "VA", "XR", "SL", "SN")


def space(t):
    return t.split()


def morph(t):
    return [x.form for x in kiwi.tokenize(t) if x.tag.startswith(KEEP)]


def ndcg10(ranked, g):  # 정답이 위에 있을수록 1에 가깝다
    dcg = sum(g.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked[:10]))
    best = sorted(g.values(), reverse=True)[:10]
    return dcg / sum(v / math.log2(i + 2) for i, v in enumerate(best))


print(f"문단 {len(docs)}개 · 질문 {len(queries)}개 · k1={k1}")
for name, tok in (("띄어쓰기", space), ("형태소", morph)):
    corpus = [tok(d["title"] + " " + d["text"]) for d in docs]
    vocab = set(w for c in corpus for w in c)
    qs = [tok(q) for _, q in queries]
    miss = sum(w not in vocab for q in qs for w in q)  # 문서 어디에도 없는 질문 조각
    index = bm25s.BM25(k1=k1)
    index.index(corpus, show_progress=False)
    ids, _ = index.retrieve(qs, k=10, show_progress=False)
    score = sum(ndcg10([docs[i]["docid"] for i in ids[j]], gold[queries[j][0]]) for j in range(len(queries))) / len(queries)
    print(f"[{name}] nDCG@10 {score:.2f} · 없는 질문 조각 {miss}/{sum(map(len, qs))}")
