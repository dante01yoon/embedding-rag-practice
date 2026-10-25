import json, sys
import bm25s, numpy as np
from kiwipiepy import Kiwi
from sentence_transformers import CrossEncoder, SentenceTransformer
sys.path.insert(0, "b3"); from chunk import split
docs = json.load(open("k8s/docs_ko.json"))
chunks = [c for d in docs for c in split(d["text"], 500, 100)]
ctx = json.load(open("k8s/ctx_ko.json"))
texts = [ctx[str(i)] + "\n" + c for i, c in enumerate(chunks)]
qa = [x for x in json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json")) if "source" in x]
gold = [{i for i, c in enumerate(chunks) if x["source"][:60] in c} for x in qa]
print(len(qa), sum(bool(g) for g in gold))
model = SentenceTransformer("BAAI/bge-m3"); kiwi = Kiwi(); rr = CrossEncoder("BAAI/bge-reranker-v2-m3")
words = lambda t: [x.form.lower() for x in kiwi.tokenize(t) if x.tag[0] in "NVS"]
vecs, vctx = np.load("k8s/vecs_ko_500.npy"), np.load("k8s/vecs_ko_ctx.npy")
bm = bm25s.BM25(); bm.index([words(t) for t in texts], show_progress=False)
def rrf(*rs, k=60):
    s = {}
    for r in rs:
        for j, i in enumerate(r): s[int(i)] = s.get(int(i), 0) + 1 / (k + j + 1)
    return sorted(s, key=s.get, reverse=True)
fail = {k: 0 for k in ["벡터", "+맥락", "+맥락 BM25", "+재순위"]}
n = 0
for x, g in zip(qa, gold):
    if not g: continue
    n += 1
    qv = model.encode(x["question"], normalize_embeddings=True)
    v = np.argsort(-(vecs @ qv))[:150]; vc = np.argsort(-(vctx @ qv))[:150]
    b = bm.retrieve([words(x["question"])], k=150, show_progress=False)[0][0]
    h = rrf(vc, b)[:150]
    s = rr.predict([(x["question"], texts[i]) for i in h]); r = [h[i] for i in np.argsort(-s)]
    for k, top in [("벡터", v), ("+맥락", vc), ("+맥락 BM25", h), ("+재순위", r)]:
        fail[k] += not (g & set(int(i) for i in top[:20]))
for k, f in fail.items(): print(k, f, n, round(f / n * 100, 1))
