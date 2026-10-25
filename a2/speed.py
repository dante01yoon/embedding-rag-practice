import time

import numpy as np
import pandas as pd

books = np.load("books/book_vecs.npy")
titles = pd.read_csv("books/books_clean.csv").title
q = books[0]
print("책 벡터:", books.shape, "  길이:", np.linalg.norm(books, axis=1)[:3].round(3))

t = time.perf_counter()
loop = [sum(float(x) * float(y) for x, y in zip(q, v)) for v in books]
loop_ms = (time.perf_counter() - t) * 1000
print("반복문:", round(loop_ms, 1), "밀리초")
t = time.perf_counter()
dots = books @ q
np_ms = (time.perf_counter() - t) * 1000
print("넘파이:", round(np_ms, 3), "밀리초  →", round(loop_ms / np_ms), "배 빠름")

dist = np.linalg.norm(books - q, axis=1)
print("내적 큰 순:", list(titles[np.argsort(-dots)[1:4]]))
print("거리 작은 순:", list(titles[np.argsort(dist)[1:4]]))
