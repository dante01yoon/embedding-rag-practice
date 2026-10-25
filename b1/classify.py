import pandas as pd
from transformers import pipeline

books = pd.read_csv("books/books_clean.csv")
FICTION = "소설|SF|판타지|추리|무협|스릴러|로맨스|동화|(?<!논)픽션|호러|공포|미스터리|희곡|만화"  # 논픽션은 빼고 픽션만
NONFICTION = "논픽션|비소설|수필|에세이|철학|백과|자서전|회고록|전기|교양|역사서|과학|경제|정치|사회|종교|자기계발|평론|인문"
genre = books["genre"].fillna("")
books["truth"] = None
books.loc[genre.str.contains(NONFICTION), "truth"] = "비소설"
books.loc[genre.str.contains(FICTION), "truth"] = "소설"  # 장르 칸에서 정답을 뽑는다 (둘 다면 소설)
print(books["truth"].value_counts())
print(books.loc[genre.str.contains("논픽션"), ["title", "genre", "truth"]].head(4))

clf = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7")
print(books["title"][338], clf(books["description"][338], ["소설", "비소설"]))

books["pred"] = [clf(d, ["소설", "비소설"])["labels"][0] for d in books["description"]]  # 가장 그럴듯한 쪽

known = books.dropna(subset=["truth"])
print("정답을 아는 책", len(known))
print("전체 정확도", round((known["pred"] == known["truth"]).mean(), 3))

for k in ("소설", "비소설"):
    part = known[known["truth"] == k]
    print(k, "맞힌 비율", round((part["pred"] == k).mean(), 2))
print("전부 소설이라고만 해도", round((known["truth"] == "소설").mean(), 3))
print(known[known["pred"] != known["truth"]][["title", "truth", "pred"]].head(6))  # 틀린 예

books["kind"] = books["truth"].fillna(books["pred"])  # 정답이 있으면 정답, 없으면 예측
books.drop(columns=["truth", "pred"]).to_csv("books/books_kind.csv", index=False)