import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

books = pd.read_csv("books/books_mood.csv")
model = SentenceTransformer("BAAI/bge-m3")
vecs = model.encode(list(books["description"]), normalize_embeddings=True)  # 책 1,307권 → 1024차원
np.save("books/book_vecs.npy", vecs)
print(vecs.shape)
