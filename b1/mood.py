import pandas as pd
from sentence_transformers import SentenceTransformer

books = pd.read_csv("books/books_kind.csv")
model = SentenceTransformer("BAAI/bge-m3")
MOODS = {
    "즐거운": "웃음이 가득한 유쾌하고 즐거운 이야기",
    "놀라운": "상상도 못한 놀라운 반전과 신기한 세계",
    "화나는": "부당함과 분노, 격렬한 갈등",
    "긴장감": "숨막히는 긴장감, 추격과 살인 사건, 스릴러",
    "슬픈": "상실과 죽음, 눈물 나는 슬프고 비극적인 이야기",
}
desc = model.encode(list(books["description"]), normalize_embeddings=True)  # 책 소개 → 벡터
mood = model.encode(list(MOODS.values()), normalize_embeddings=True)  # 분위기 문장 → 벡터
score = desc @ mood.T  # 코사인 유사도 (책 수 × 분위기 5개)
score = score - score.mean(axis=0)  # 분위기마다 평균을 빼서 '평소보다 얼마나 더'로 맞춘다
print(score.mean(axis=0).round(3))
print(pd.Series(score.argmax(axis=1)).map(dict(enumerate(MOODS))).value_counts())

for i, name in enumerate(MOODS):
    books[name] = score[:, i].round(3)
    print(name, list(books.sort_values(name, ascending=False)["title"].head(3)))
books.to_csv("books/books_mood.csv", index=False)