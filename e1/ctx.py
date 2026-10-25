import json
import sys
import time

import bm25s
import numpy as np
from kiwipiepy import Kiwi
from sentence_transformers import CrossEncoder, SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [c for d in docs for c in split(d["text"], 500, 100)]
ctx = json.load(open("k8s/ctx_ko.json"))  # 맥락 검색 수업에서 LLM으로 만든 청크별 맥락
texts = [ctx[str(i)] + "\n" + c for i, c in enumerate(chunks)]
qa = [x for x in json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json")) if "source" in x]
gold = [{i for i, c in enumerate(chunks) if x["source"][:60] in c} for x in qa]  # 정답 문장이 든 청크
model = SentenceTransformer("BAAI/bge-m3")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
kiwi = Kiwi()
vecs, vecs_ctx = np.load("k8s/vecs_ko_500.npy"), np.load("k8s/vecs_ko_ctx.npy")


def words(t):
    return [x.form.lower() for x in kiwi.tokenize(t) if x.tag[0] in "NVS"]


bm = bm25s.BM25()
bm.index([words(t) for t in texts], show_progress=False)


def rrf(*rankings, k=60):
    s = {}
    for r in rankings:
        for j, i in enumerate(r):
            s[int(i)] = s.get(int(i), 0) + 1 / (k + j + 1)
    return sorted(s, key=s.get, reverse=True)


N = 150  # 재순위에 넘길 후보 수
fail, sec = {"벡터": 0, "+ 맥락": 0, "+ 맥락 BM25": 0, "+ 재순위": 0}, 0
for x, g in zip(qa, gold):
    qv = model.encode(x["question"], normalize_embeddings=True)
    v, vc = np.argsort(-(vecs @ qv))[:150], np.argsort(-(vecs_ctx @ qv))[:150]
    b = bm.retrieve([words(x["question"])], k=150, show_progress=False)[0][0]
    h = rrf(vc, b)
    t = time.time()
    cand = h[:N]
    s = reranker.predict([(x["question"], texts[i]) for i in cand])
    r = [cand[i] for i in np.argsort(-s)]
    sec += time.time() - t
    for name, top in zip(fail, [v, vc, h, r]):
        fail[name] += not (g & {int(i) for i in top[:20]})  # 상위 20개 안에 정답 청크가 없으면 실패
print(f"질문 {len(qa)}개 · 상위 20개 실패율")
for name, f in fail.items():
    print(f"  {name:<10} {f / len(qa) * 100:4.1f}%")
print(f"재순위 후보 {N}개 · 질문당 {sec / len(qa):.2f}초")
