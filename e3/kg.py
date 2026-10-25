import json
import re
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
qa = json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json"))  # 질문마다 정답 문서 path
model = SentenceTransformer("BAAI/bge-m3")


def mrr(units, vecs):  # 문서 단위 MRR@10: 질문과 가장 가까운 단위들 → 처음 나온 정답 문서의 순위
    got = []
    for x in qa:
        seen = []
        for i in np.argsort(-(vecs @ model.encode(x["question"], normalize_embeddings=True))):
            if units[i][0] not in seen:
                seen.append(units[i][0])
            if len(seen) == 10:
                break
        got.append(1 / (seen.index(x["path"]) + 1) if x["path"] in seen else 0)
    return np.mean(got)


flat = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]  # 1) 평평하게: 500자 청크
print(f"평평한 청크 | 단위 {len(flat):,}개 · MRR@10 {mrr(flat, np.load('k8s/vecs_ko_500.npy')):.3f}")


def sections(d):  # 2) 구조 그대로: 제목마다 노드 하나, 위치(문서 제목 > 절 제목)를 기억
    out, head = [], d["title"]
    for part in re.split(r"\n(?=#{2,4} )", d["text"]):
        m = re.match(r"#{2,4} (.+)", part)
        if m:
            head = m.group(1).strip()
        out.append((d["path"], d["title"], head, part))
    return out


nodes = [s for d in docs for s in sections(d)]
units = [(p, f"{t} > {h}\n{c}") for p, t, h, body in nodes for c in split(body, 500, 100)]  # 긴 절은 잘게 · 청크마다 위치(문서 > 절)를 앞에
print(f"구조 노드  | 단위 {len(units):,}개 · MRR@10 {mrr(units, model.encode([u for _, u in units], normalize_embeddings=True, batch_size=32)):.3f}")
