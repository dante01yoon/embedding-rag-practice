import time

import chromadb
import faiss
import numpy as np
import pandas as pd
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

books = pd.read_csv("books/books_mood.csv")
vecs = np.load("books/book_vecs.npy")  # embed_books.py로 미리 만든 벡터 (1,307 × 1024)
q = SentenceTransformer("BAAI/bge-m3").encode("전쟁의 상처를 견디는 가족", normalize_embeddings=True)


def show(name, idx, sec):
    print(f"{name:9s} {sec * 1000:6.1f}ms ", list(books["title"].iloc[idx]))


# 1) FAISS: 파이썬 안에서 도는 검색 라이브러리
index = faiss.IndexFlatIP(1024)
index.add(vecs)
t = time.perf_counter()
_, ids = index.search(q[None], 3)
show("FAISS", ids[0], time.perf_counter() - t)

# 2) Chroma: 파일로 저장되는 가벼운 벡터 DB
col = chromadb.PersistentClient("books/chroma_b2").get_or_create_collection("books", metadata={"hnsw:space": "cosine"})
col.upsert(ids=[str(i) for i in range(len(books))], embeddings=vecs)
t = time.perf_counter()
res = col.query(query_embeddings=[q], n_results=3)
show("Chroma", [int(i) for i in res["ids"][0]], time.perf_counter() - t)

# 3) pgvector: PostgreSQL에 벡터 칸을 더한 것 (Docker로 띄운 DB)
db = psycopg.connect("postgresql://postgres@127.0.0.1:5433/postgres", autocommit=True)
db.execute("CREATE EXTENSION IF NOT EXISTS vector")
register_vector(db)
db.execute("DROP TABLE IF EXISTS books")
db.execute("CREATE TABLE books (id int PRIMARY KEY, title text, kind text, embedding vector(1024))")
with db.cursor().copy("COPY books (id, title, kind, embedding) FROM STDIN WITH (FORMAT BINARY)") as cp:
    cp.set_types(["int4", "text", "text", "vector"])
    for i, (title, kind) in enumerate(zip(books["title"], books["kind"])):
        cp.write_row([i, title, kind, vecs[i]])
db.execute("CREATE INDEX ON books USING hnsw (embedding vector_cosine_ops)")
t = time.perf_counter()
rows = db.execute("SELECT id FROM books ORDER BY embedding <=> %s LIMIT 3", (q,)).fetchall()
show("pgvector", [r[0] for r in rows], time.perf_counter() - t)
