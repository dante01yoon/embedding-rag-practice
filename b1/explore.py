import matplotlib.pyplot as plt
import pandas as pd
plt.rcParams["font.family"] = "AppleGothic"  # 한글 글꼴 (윈도우: Malgun Gothic)

books = pd.read_csv("books/books_ko_raw.csv")
print(books.shape)
print(books[["title", "author", "genre", "published"]].head(3))

print(books.isna().sum())
print(books["genre"].value_counts().head(5))

books["words"] = books["description"].fillna("").str.split().str.len()
print(books["words"].describe())

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ax[0].imshow(books[["title", "author", "genre", "published", "description"]].isna().T, aspect="auto", cmap="gray_r", interpolation="nearest")
ax[0].set_yticks(range(5), ["제목", "저자", "장르", "출판", "소개"])
ax[0].set_title("빈 칸 지도 (검은 줄 = 비어 있음)")
ax[1].hist(books["words"].clip(upper=300), bins=40)
ax[1].set_title("소개 글 길이 (어절 수)")
plt.tight_layout()
plt.savefig("b1/explore.png", dpi=100)
print("저장: b1/explore.png")
