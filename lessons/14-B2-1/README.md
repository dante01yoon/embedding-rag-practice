# 14. 벡터 저장소 세 가지: FAISS · Chroma · pgvector

> B2 · 벡터 저장소 · 수업 14 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- FAISS는 프로그램 안의 라이브러리, Chroma는 폴더에 저장되는 가벼운 벡터 DB, pgvector는 PostgreSQL 서버의 확장이에요. 같은 벡터를 넣으면 같은 결과가 나와요.
- Connection refused는 서버가 안 켜졌다는 뜻이고, 속도는 작은 데이터로는 비교할 수 없어요. 고르는 기준은 규모, 이미 쓰는 시스템, 필요한 기능이에요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b2/start_db.sh`](../../b2/start_db.sh) | pgvector가 든 PostgreSQL을 Docker로 띄우기 |
| [`b2/stores.py`](../../b2/stores.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`b2/embed_books.py`](../../b2/embed_books.py) | 책 소개 글 1,307개를 bge-m3 벡터로 바꿔 books/book_vecs.npy로 저장 (처음 한 번) |

읽는 데이터: [`books/books_mood.csv`](../../books/books_mood.csv)

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python b2/embed_books.py
```

수업 명령:

```bash
uv run python b2/stores.py
sh b2/start_db.sh
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

pgvector 쪽 SQL에 WHERE kind 등호 비소설을 넣어서, 비소설 중에서만 찾아보세요. 결과가 어떻게 바뀌는지, 그리고 왜 그런지 생각해 보세요.

## 풀이

<details><summary>풀이 보기</summary>

검색 SQL의 ORDER BY 앞에 WHERE kind 등호 비소설을 넣어요. 다른 표 조건과 벡터 검색을 SQL 한 줄로 묶는 게 pgvector의 장점이에요.
결과는 타인의 고통, 힐빌리의 노래, 누가 내 치즈를 옮겼을까예요. 서부 전선 이상 없다와 나무들 비탈에 서다는 소설이라 빠졌어요.
세 번째 책은 질문과 꽤 멀어 보이죠. 비소설 중에는 전쟁과 가족을 다룬 책이 적어서, 조건을 걸면 덜 비슷한 책까지 내려가요. 다음 수업에서 이 거르기를 자세히 봐요.

영상에서 입력한 그대로입니다.

- `b2/stores.py`를 엽니다.
- 46행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
rows = db.execute("SELECT id FROM books WHERE kind = '비소설' ORDER BY embedding <=> %s LIMIT 3", (q,)).fetchall()
```

- 실행: `uv run python b2/stores.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
