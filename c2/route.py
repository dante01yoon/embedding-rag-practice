import json
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
sys.path.insert(0, "c2")
from agent import QA, agent, cache, CACHE, chat, right  # noqa: E402
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [c for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
model = SentenceTransformer("BAAI/bge-m3")
NOANS = "자료에 없습니다."
PROMPT = "아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"


def rag(q):  # 싼 길: 벡터 검색 청크 4개
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:4]
    m = chat([{"role": "user", "content": PROMPT.format(ctx="\n\n".join(chunks[i] for i in top), q=q)}])
    return m["content"].strip(), m["tokens"]


def route(q):  # 검색으로 먼저 답하고, 모르겠다고 하면 에이전트로
    a, t = rag(q)
    if NOANS not in a:
        return a, t, False
    a2, _, t2 = agent(q)
    return a2, t + t2, True


res = [(x, *rag(x["question"])) for x in QA]
print(f"검색만          | 맞힘 {sum(right(x, a) for x, a, _ in res)}/{len(QA)} · 입력 평균 {np.mean([t for _, _, t in res]):,.0f}토큰")
runs = [agent(x["question"]) for x in QA]
print(f"에이전트만      | 맞힘 {sum(right(x, a) for x, (a, _, _) in zip(QA, runs))}/{len(QA)} · 입력 평균 {np.mean([r[2] for r in runs]):,.0f}토큰")
res = [(x, *route(x["question"])) for x in QA]
print(f"검색 → 에이전트 | 맞힘 {sum(right(x, a) for x, a, _, _ in res)}/{len(QA)} · 입력 평균 {np.mean([r[2] for r in res]):,.0f}토큰 · 에이전트로 넘김 {sum(r[3] for r in res)}개")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
