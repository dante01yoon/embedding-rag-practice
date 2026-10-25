import chromadb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

books = pd.read_csv("books/books_mood.csv")
vecs = np.load("books/book_vecs.npy")
model = SentenceTransformer("BAAI/bge-m3")
client = chromadb.PersistentClient("books/chroma_b2")
col = client.get_or_create_collection("books_meta", metadata={"hnsw:space": "cosine"})
col.upsert(ids=[str(i) for i in range(len(books))], embeddings=vecs, metadatas=[{"kind": k} for k in books["kind"]])  # 책마다 종류를 메타데이터로


def titles(res):
    return list(books["title"].iloc[[int(i) for i in res["ids"][0]]])


q = model.encode("병과 싸운 소녀가 쓴 실제 일기", normalize_embeddings=True)
print(col.get(ids=["0"])["metadatas"])
print(titles(col.query(query_embeddings=[q], n_results=6, where={"kind": "비소설"})))

for query in ["병과 싸운 소녀가 쓴 실제 일기", "마법 학교에서 친구들과 모험하는 이야기"]:
    q = model.encode(query, normalize_embeddings=True)
    res = col.query(query_embeddings=[q], n_results=6)  # 나중에 거르기: 6권 찾고 → 비소설만 남긴다
    after = [t for t, m in zip(titles(res), res["metadatas"][0]) if m["kind"] == "비소설"]
    pre = col.query(query_embeddings=[q], n_results=6, where={"kind": "비소설"})  # 먼저 거르기: 비소설 안에서 6권
    print(query, "· 전체 6권 거리", [round(d, 2) for d in res["distances"][0]])
    print(f"  나중에 거르기 {len(after)}권", after)
    print(f"  먼저 거르기   {len(titles(pre))}권", [f"{t} {d:.2f}" for t, d in zip(titles(pre), pre["distances"][0])])
