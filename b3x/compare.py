import json
import re
import sys

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
QA = ["k8s/qa_sent.json"]  # 원문 문장에서 뽑은 질문 (어떤 자르기와도 무관)
qa = [x for f in QA for x in json.load(open(f)) if "source" in x]
model = SentenceTransformer("BAAI/bge-m3")
norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731  띄어쓰기·줄바꿈 차이는 무시


def sentences(t):  # 문단 안 줄바꿈은 이어 붙이고 문장으로 나누기
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)
    return [s.strip() for s in re.split(r"(?<=[.다?!])\s+|\n\n+", t) if s.strip()]


def fixed(t):  # 1) 고정 길이: 500자마다 뚝뚝, 100자 겹침
    return [t[i:i + 500] for i in range(0, max(1, len(t) - 100), 400)]


def paragraph(t):  # 2) 문단: 지금까지 쓴 방법
    return split(t, 500, 100)


rec = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100, separators=["\n## ", "\n### ", "\n\n", "\n", ". ", "다. ", " ", ""])


def recursive(t):  # 3) 재귀: 큰 경계(제목 → 문단 → 줄 → 문장)부터 차례로
    return rec.split_text(t)


def semantic(t):  # 4) 의미: 이웃 문장의 뜻이 크게 달라지는 곳에서
    ss = sentences(t)
    if len(ss) < 3:
        return [" ".join(ss)] if ss else []
    v = model.encode(ss, normalize_embeddings=True, batch_size=64)
    sim = (v[:-1] * v[1:]).sum(1)  # 이웃 문장끼리의 비슷함
    cut, out, cur = np.percentile(sim, 15), [], ss[0]
    for s, d in zip(ss[1:], sim):
        if d < cut or len(cur) + len(s) > 900:
            out.append(cur)
            cur = s
        else:
            cur += " " + s
    return out + [cur]


def cover(source, ctx):  # 정답 문장이 넘긴 글에 통째로 들어 있는 비율
    ss = [norm(s) for s in sentences(source)]
    ss = ss[1:-1] if len(ss) > 2 else ss  # 앞뒤 잘린 문장은 빼고
    return np.mean([s in norm(ctx) for s in ss])


def evaluate(name, units, find):  # 질문마다 2,000자만 넘기고 정답 문장 포함률
    vecs = model.encode([u for u, _ in units], normalize_embeddings=True, batch_size=32)
    got = []
    for x in qa:
        ctx = find(np.argsort(-(vecs @ model.encode(x["question"], normalize_embeddings=True))), units)[:2000]
        got.append(cover(x["source"], ctx))
    print(f"{name:<8} | 청크 {len(units):5,}개 · 정답 문장 {np.mean(got) * 100:4.1f}%")


plain = lambda order, units: "".join(units[i][1] for i in order[:50])  # noqa: E731  위에서부터 이어 붙이기
for name, make in [("고정 길이", fixed), ("문단", paragraph), ("재귀", recursive), ("의미", semantic)]:
    units = [(c, c) for d in docs for c in make(d["text"])]
    evaluate(name, units, plain)

# 5) 계층: 작은 청크(200자)로 찾고, 그 청크가 속한 제목 구역 전체를 넘긴다
parents = [sec for d in docs for sec in re.split(r"\n(?=#{2,4} )", d["text"]) if sec.strip()]
kids = [(p[i:i + 200], p) for p in parents for i in range(0, max(1, len(p) - 40), 160)]  # (작은 청크, 부모 구역)


def up(order, units):  # 찾은 작은 청크 → 부모 구역 (중복 없이)
    seen = []
    for i in order:
        if units[i][1] not in seen:
            seen.append(units[i][1])
        if len("".join(seen)) >= 2000:
            break
    return "".join(seen)


evaluate("계층", kids, up)
