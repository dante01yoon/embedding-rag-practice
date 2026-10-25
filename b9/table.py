import base64
import io
import json
import os
import re
import sys

import numpy as np
import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "pdf/llm_cache_b9.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(content, key):  # 그림이 든 질문도 받도록 content와 캐시 열쇠를 따로
    if key not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": content}], temperature=0)
        cache[key] = r.choices[0].message.content.strip()
    return cache[key]


PDF = "pdf/irs_p501.pdf"
pages = [p.extract_text() for p in PdfReader(PDF).pages]
chunks = [(n, c) for n, t in enumerate(pages) for c in split(t, 500, 100)]
model = SentenceTransformer("BAAI/bge-m3")
plumb = pdfplumber.open(PDF)

Q, rows = [], []  # 질문(정답 금액이 있는) · 표를 행마다 풀어 쓴 문장
status = None
for r in plumb.pages[1].extract_tables()[0][1:11]:  # 2쪽 신고 기준표: 빈 칸은 위 칸의 신고 유형
    status = r[0] or status
    Q.append((f"filing status가 {status.replace('***', '')}이고 2025년 말 {r[1]}일 때, 소득이 얼마 이상이면 신고해야 하나요?", r[2], 1))
    rows.append(f"[2025 신고 기준표] filing status: {status} / 나이: {r[1]} / 이 금액 이상이면 신고: {r[2]}")
for r in plumb.pages[24].extract_tables()[1][2:7]:  # 25쪽 표준공제표: 한 칸에 "1 2 3 4"와 금액 네 개가 뭉쳐 있다
    for n, v in zip(r[1].split(), r[2].replace("$", "").split()):
        Q.append((f"filing status가 {r[0].replace('**', '')}이고 65세 이상·시각장애 체크 박스가 {n}개일 때 standard deduction은 얼마인가요?", "$" + v, 24))
        rows.append(f"[표준공제 65세 이상·시각장애 표] filing status: {r[0]} / 체크 박스 {n}개 / standard deduction: ${v}")


enc = {}


def top(items, q, k):  # items 중 질문과 가까운 k개 (벡터는 한 번만 만든다)
    key = tuple(items)
    if key not in enc:
        enc[key] = model.encode(list(items), normalize_embeddings=True)
    v = enc[key]
    return [items[i] for i in np.argsort(-(v @ model.encode(q, normalize_embeddings=True)))[:k]]


def by_text(q):  # 1) 쪽 글자를 청크로 잘라 검색
    ctx = "\n\n".join(top([c for _, c in chunks], q, 4))
    p = f"아래 자료만 보고 금액 하나로 답하세요.\n\n{ctx}\n\n질문: {q}"
    return ask(p, p)


def by_rows(q):  # 2) 표를 행 문장으로 풀어 함께 검색
    ctx = "\n".join(top(rows, q, 4) + top([c for _, c in chunks], q, 2))
    p = f"아래 자료만 보고 금액 하나로 답하세요.\n\n{ctx}\n\n질문: {q}"
    return ask(p, p)


def by_image(q):  # 3) 검색으로 찾은 쪽을 그림으로 보여 주기
    best = top([c for _, c in chunks], q, 1)[0]
    pn = next(n for n, c in chunks if c == best)
    buf = io.BytesIO()
    plumb.pages[pn].to_image(resolution=110).original.save(buf, format="PNG")
    img = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return ask([{"type": "text", "text": f"이 쪽 그림만 보고 금액 하나로 답하세요.\n\n질문: {q}"}, {"type": "image_url", "image_url": {"url": img}}], f"IMG{pn}|{q}"), pn


def hit(gold, answer):
    return gold.replace("$", "") in answer.replace("$", "")


score = {"글자": 0, "행 문장": 0, "그림": 0}
for q, gold, pn in Q:
    score["글자"] += hit(gold, by_text(q))
    score["행 문장"] += hit(gold, by_rows(q))
    score["그림"] += hit(gold, by_image(q)[0])
print(f"질문 {len(Q)}개 · 맞힌 수", score)

NONE = "자료 없이, 아는 대로 금액 하나로만 답하세요. IRS Publication 501 (2025) 기준.\n\n질문: {q}"
print("자료 없이", sum(hit(gold, ask(NONE.format(q=q), NONE.format(q=q))) for q, gold, _ in Q))  # 기준선: 모델이 외운 것


def shift(s):  # 반사실 시험: 자료 속 금액을 모두 1,000달러 올린다 (외운 값으로는 못 맞히게)
    return re.sub(r"\$?(\d{1,2}),(\d{3})", lambda m: "$" + format(int(m.group(1) + m.group(2)) + 1000, ","), s)


chunks = [(n, shift(c)) for n, c in chunks]
rows = [shift(t) for t in rows]
moved = {"글자": 0, "행 문장": 0, "자료 없이": 0}
for q, gold, pn in Q:
    new = shift(gold)
    moved["글자"] += hit(new, by_text(q))
    moved["행 문장"] += hit(new, by_rows(q))
    moved["자료 없이"] += hit(new, ask(NONE.format(q=q), NONE.format(q=q)))
print("금액을 바꾼 자료", moved)
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
