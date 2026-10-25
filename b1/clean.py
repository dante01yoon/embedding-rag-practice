import pandas as pd

books = pd.read_csv("books/books_ko_raw.csv")
books = books.replace("값찾기", None)  # 위키백과 틀이 값을 못 채운 자리 → 빈 칸
print(books["genre"].value_counts().head(3))

junk = books["author"].str.contains("{{", regex=False, na=False)
books["author"] = books["author"].str.split("{{", regex=False).str[0].str.strip(" (")
books = books.replace("", None)  # 잘라 내고 아무것도 안 남은 칸도 빈 칸으로
print(books.loc[junk, "author"])

books = books.dropna(subset=["description"])  # 소개 글이 없는 책은 뺀다
books["words"] = books["description"].str.split().str.len()
books = books[books["words"] >= 20]  # 20어절이 안 되는 짧은 소개 글도 뺀다
print("남은 책", len(books))

books["tagged"] = books["pageid"].astype(str) + " " + books["description"]  # 앞에 책 번호를 붙여 둔다
books.to_csv("books/books_clean.csv", index=False)
open("books/tagged_description.txt", "w").write("\n".join(books["tagged"]))
