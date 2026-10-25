import json
import os
import re

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()
llm = OpenAI()
CACHE = "books/llm_cache_c1.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


books = pd.read_csv("books/books_mood.csv")
vecs = np.load("books/book_vecs.npy")
model = SentenceTransformer("BAAI/bge-m3")
author = books["author"].fillna("").str.strip()
names = [a for a, n in author.value_counts().items() if a and n >= 5 and a != "미상" and "[[" not in a][:14]  # 책이 5권 넘는 작가 14명


def by_rag(q, k):  # 검색해서 k권만 보여 주고 세게 하기
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:k]
    ctx = "\n".join(f"- {books.title[i]} / 작가: {books.author[i]}" for i in top)
    answer = ask(f"아래 도서 목록만 보고 숫자 하나로만 답하세요.\n\n{ctx}\n\n질문: {q}")
    return int(re.search(r"\d+", answer).group())


for k in (4, 20):
    right = sum(by_rag(f"이 도서 목록에 {a}의 책은 모두 몇 권인가요?", k) == (author == a).sum() for a in names)
    print(f"검색 {k:2d}권 보여 주고 세기 | 맞힘 {right}/{len(names)}")


def by_table(q):  # 집계는 표에서: 질문에서 작가 이름만 뽑아 그 칸을 센다
    name = ask(f"다음 질문에 나오는 작가 이름만 출력하세요.\n\n{q}")
    return int((author == name).sum())


right = sum(by_table(f"이 도서 목록에 {a}의 책은 모두 몇 권인가요?") == (author == a).sum() for a in names)
print(f"표에서 세기 | 맞힘 {right}/{len(names)}")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
