import json
import os
import re

import networkx as nx
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()
llm = OpenAI()
CACHE = "books/llm_cache_b9.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


books = pd.read_csv("books/books_mood.csv")
vecs = np.load("books/book_vecs.npy")
model = SentenceTransformer("BAAI/bge-m3")

G = nx.Graph()  # 책 · 작가 · 장르를 점으로, 관계를 선으로
for _, b in books.iterrows():
    G.add_node(b["title"], kind="book")
    if isinstance(b["author"], str) and b["author"].strip():
        G.add_edge(b["title"], "작가:" + b["author"].strip())
    for g in str(b["genre"]).split(","):
        if g.strip() and g.strip() != "nan":
            G.add_edge(b["title"], "장르:" + g.strip())
print(f"점 {G.number_of_nodes()}개 · 선 {G.number_of_edges()}개")


def by_vector(q, k):  # 벡터 검색: 뜻이 가까운 책 k권
    return list(books["title"].iloc[np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:k]])


def by_graph(q):  # 그래프 검색: 질문의 작가 점에 이어진 책들
    name = ask(f"다음 질문에 나오는 작가 이름만 출력하세요.\n\n{q}")
    nodes = [n for n in G if n.startswith("작가:") and name in n]  # "헤밍웨이" → "작가:어니스트 헤밍웨이" (이름이 들어간 작가 점 전부)
    return list({book for n in nodes for book in G.neighbors(n)}), name


author = books["author"].fillna("").str.strip()
authors = [a for a, n in author.value_counts().items() if a and n >= 3 and a != "미상"]  # 책이 3권 이상인 작가
vr, gr, gp = [], [], []  # 벡터 재현율 · 그래프 재현율 · 그래프 정밀도
for a in authors:
    truth = set(books["title"][author == a])
    q = re.sub(r"\[\[|\s*\(.*?\)", "", a).split()[-1] + " 책 다 알려 줘"  # "[[김훈 (소설가)" → "김훈 책 다 알려 줘"
    vr.append(len(truth & set(by_vector(q, len(truth)))) / len(truth))
    found, name = by_graph(q)
    gr.append(len(truth & set(found)) / len(truth))
    gp.append(len(truth & set(found)) / max(len(found), 1))  # 찾은 것 중 맞는 비율
    if gr[-1] < 1:
        print(f"  놓침: {q} → LLM '{name}' · {gr[-1]:.0%}")
print(f"작가 {len(authors)}명 · '○○ 책 다 알려 줘' | 그 작가 책을 찾은 비율: 벡터 {np.mean(vr):.2f} · 그래프 {np.mean(gr):.2f} · 그래프가 찾은 것 중 맞는 비율 {np.mean(gp):.2f}")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
