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
CACHE = "books/llm_cache.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):  # 지난 수업의 캐시 그대로
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


books = pd.read_csv("books/books_mood.csv")
year = books["published"].astype(str).str.extract(r"(\d{4})")[0].astype(float)  # "1987년 11월 14일" → 1987, 없으면 NaN
vecs = np.load("books/book_vecs.npy")
model = SentenceTransformer("BAAI/bge-m3")


def route(q):  # 라우팅: 어디서 찾을지 고르기
    return ask(f"다음 질문이 쿠버네티스 문서에 대한 질문이면 k8s, 책 추천 요청이면 books라고 한 단어로만 답하세요.\n\n{q}")


for q in ["emptyDir 볼륨의 저장소는 어디에서 제공되나요?", "파드가 계속 재시작돼요", "전쟁의 상처를 견디는 가족 이야기 추천해 줘", "비 오는 날 읽기 좋은 소설", "쿠버네티스 입문서 추천해 줘"]:
    print(f"{route(q):6s} ← {q}")

SELF = '책 추천 요청에서 조건을 뽑아 JSON으로만 답하세요. {"query": 검색할 내용, "kind": "소설" 또는 "비소설" 또는 null, "year_min": 숫자 또는 null, "year_max": 숫자 또는 null}\n\n'


def conditions(q):  # 셀프 쿼리: 질문에서 조건 뽑기
    raw = ask(SELF + q)
    return json.loads(re.search(r"\{.*\}", raw, re.S).group())  # ```json 울타리 안의 { … }만 꺼낸다


def keep(f):  # 조건에 맞는 책만 True
    ok = np.ones(len(books), bool)
    if f["kind"]:
        ok &= (books["kind"] == f["kind"]).values
    if f["year_min"]:
        ok &= (year >= f["year_min"]).values
    if f["year_max"]:
        ok &= (year <= f["year_max"]).values
    return ok


Q = ["2010년 이후에 나온 SF 소설 추천해 줘", "1900년 이전에 쓰인 고전 소설", "2000년대에 나온 과학 교양서", "19세기 추리 소설 읽고 싶어",
     "최근 10년 안에 나온 판타지 소설", "1950년 이전에 출간된 철학 책", "1990년대 일본 소설", "2020년 이후에 나온 에세이"]
total = [0, 0]
for q in Q:
    f = conditions(q)
    ok = keep(f)
    plain = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:5]  # 그냥 벡터 검색
    scores = vecs @ model.encode(f["query"], normalize_embeddings=True)
    picked = [i for i in np.argsort(-scores) if ok[i]][:5]  # 조건으로 거른 뒤 벡터 검색
    total[0] += ok[plain].sum()
    total[1] += ok[picked].sum()
    print(f"{q} → {f['kind']} {f['year_min']}~{f['year_max']} | 그냥 {ok[plain].sum()}/5 · 셀프 쿼리 {ok[picked].sum()}/5")
print(f"조건을 지킨 책: 그냥 {total[0]}/40 · 셀프 쿼리 {total[1]}/40")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
