import csv
import json
import os
import re

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()
llm = OpenAI()
CACHE = "books/llm_cache_e5.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


books = list(csv.DictReader(open("books/books_clean.csv")))  # 사내 문서 대신: 도서 1,307권의 소개 글
model = SentenceTransformer("BAAI/bge-m3")
VEC = "books/vecs_desc.npy"
if not os.path.exists(VEC):
    np.save(VEC, model.encode([f'{b["title"]}\n{b["description"]}' for b in books], normalize_embeddings=True, batch_size=16))
vecs = np.load(VEC)
Q = "휴고상을 받은 책을 모두 알려줘"
GOLD = set(json.load(open("e5/gold_hugo.json")))  # 소개 글에 '휴고상 수상'이라고 적힌 책 (후보만 오른 책은 제외)


def titles(ans):  # 답에 나온 제목 → 책
    return {b["title"] for b in books if b["title"] in ans}


def score(name, got):
    print(f"{name} | 맞힘 {len(got & GOLD)}/{len(GOLD)} · 잘못 넣음 {len(got - GOLD)}")


def lookup(q, k):  # 조회형: 가까운 책 k권 → 한 번에 답
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:k]
    ctx = "\n\n".join(f'[{books[i]["title"]}] {books[i]["description"]}' for i in top)
    return titles(ask(f"자료:\n{ctx}\n\n자료에 근거해서 답하세요. 제목은 [ ] 안의 표기 그대로.\n질문: {q}"))


score("조회형 top-10", lookup(Q, 10))
score("조회형 top-50", lookup(Q, 50))


def scan(q):  # 집계형 1단계: 검색어를 뽑아 그 낱말이 든 책을 전부 모은다 (top-k 아님)
    kw = ask(f"아래 질문의 대상이 문서 본문에 그대로 적혀 있을 짧은 낱말 하나만 출력하세요. 예: 상 이름, 사람 이름.\n질문: {q}").strip("\"' ")
    return kw, [b for b in books if kw in b["description"]]


def extract(q, part):  # 집계형 2단계: 몇 권씩 나눠 질문에 맞는 책만 고른다
    ctx = "\n\n".join(f'[{b["title"]}] {b["description"]}' for b in part)
    return titles(ask(f"자료:\n{ctx}\n\n질문에 해당하는 책의 제목만 [ ] 표기 그대로 한 줄에 하나씩 출력하세요. 없으면 '없음'.\n질문: {q}"))


kw, docs = scan(Q)
print(f"전체 스캔 | 검색어 '{kw}' · 책 {len(docs)}권")
score("집계형 한 번에", extract(Q, docs))
got = set().union(*[extract(Q, docs[i:i + 8]) for i in range(0, len(docs), 8)])  # 몇 권씩 나눠 고르고 코드가 합친다
score("집계형 8권씩", got)
src = sorted((b["title"], b["pageid"]) for b in docs if b["title"] in got)  # 출처 목록은 LLM이 아니라 코드가 만든다
if src:
    print("  출처: " + " · ".join(f"{t}(문서 {p})" for t, p in src[:3]) + f" 외 {len(src) - 3}권")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
