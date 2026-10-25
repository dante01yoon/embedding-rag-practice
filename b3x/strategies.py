import json
import os
import re
import time

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

docs = json.load(open("k8s/docs_ko.json"))
QA = os.environ.get("QA", "chunk")  # chunk: 문단 청크에서 만든 질문 · sent: 원문 문장에서 뽑은 질문
qa = json.load(open("k8s/qa_sent.json")) if QA == "sent" else [x for x in json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json")) if "source" in x]
model = SentenceTransformer("BAAI/bge-m3")
norm = lambda s: re.sub(r"\s+", "", s)  # 줄바꿈·띄어쓰기 차이는 무시하고 비교


def fixed(t, size=500, over=100):  # 글자 수로 뚝뚝
    return [t[i:i + size] for i in range(0, max(1, len(t) - over), size - over)]


rec = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100, separators=["\n## ", "\n### ", "\n\n", "\n", ". ", "다. ", " ", ""])


def recursive(t):  # 큰 경계(제목 → 문단 → 줄 → 문장)부터 차례로 시도
    return rec.split_text(t)


def sentences(t):
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)  # 문단 안의 줄바꿈은 이어 붙이기
    return [s.strip() for s in re.split(r"(?<=[.다?!])\s+|\n\n+", t) if s.strip()]


def semantic(t, pct=15, max_len=900):  # 이웃 문장끼리 뜻이 크게 달라지는 곳에서 자르기
    ss = sentences(t)
    if len(ss) < 3:
        return ["\n".join(ss)] if ss else []
    v = model.encode(ss, normalize_embeddings=True, batch_size=64)
    sim = (v[:-1] * v[1:]).sum(1)
    cut = np.percentile(sim, pct)
    out, cur = [], ss[0]
    for s, d in zip(ss[1:], sim):
        if d < cut or len(cur) + len(s) > max_len:
            out.append(cur)
            cur = s
        else:
            cur += " " + s
    return out + [cur]


def sections(t):  # 제목(##, ###)마다 부모 구역
    parts = re.split(r"\n(?=#{2,4} )", t)
    return [p for p in parts if p.strip()]


BUDGET = 2000  # 넘기는 글자 수


def cover(source, ctx):  # 정답 글의 문장 중 넘긴 글에 들어 있는 비율 (앞뒤 잘린 문장은 빼고)
    if len(sentences(source)) <= 2:  # 정답이 문장 하나면 그 문장이 통째로 들어 있어야
        return norm(source) in norm(ctx)
    ss = [norm(s) for s in sentences(source)[1:-1] if len(norm(s)) >= 15]
    return sum(s in norm(ctx) for s in ss) / len(ss) if ss else norm(source)[:30] in norm(ctx)


def run(name, make, k=4):
    t0 = time.time()
    if name == "계층(작게 찾고 크게 주기)":
        parents, kids = [], []
        for d in docs:
            for sec in sections(d["text"]):
                parents.append(sec)
                kids += [(len(parents) - 1, c) for c in fixed(sec, 200, 40)]
        vecs = model.encode([c for _, c in kids], normalize_embeddings=True, batch_size=32)
        units = parents
    else:
        units = [c for d in docs for c in make(d["text"])]
        vecs = model.encode(units, normalize_embeddings=True, batch_size=32)
    hit, fair, size = 0, 0, []
    for x in qa:
        s = vecs @ model.encode(x["question"], normalize_embeddings=True)
        if name == "계층(작게 찾고 크게 주기)":
            order = []
            for i in np.argsort(-s):
                p = kids[i][0]
                if p not in order:
                    order.append(p)
                if len(order) == 20:
                    break
            got = order[:k]
        else:
            got = list(np.argsort(-s)[:k])
            order = list(np.argsort(-s)[:50])
        ctx = "".join(units[i] for i in got)
        hit += norm(x["source"][:60]) in norm(ctx)
        size.append(len(ctx))
        budget = "".join(units[i] for i in order)[:BUDGET]  # 공정하게: 모두 같은 글자 수만 넘긴다
        fair += cover(x["source"], budget)
    print(f"{name:<16} | 청크 {len(units):5,}개 · 처음 기준 {hit}/{len(qa)} (평균 {np.mean(size):5,.0f}자) · 정답 문장 {fair / len(qa) * 100:4.1f}% · {time.time() - t0:4.0f}초")


if __name__ == "__main__":
    for name, make in [("고정 길이", fixed), ("문단(지금까지)", None), ("재귀", recursive), ("의미", semantic), ("계층(작게 찾고 크게 주기)", None)]:
        if name == "문단(지금까지)":
            import sys
            sys.path.insert(0, "b3")
            from chunk import split
            make = lambda t: split(t, 500, 100)  # noqa: E731
        run(name, make)
