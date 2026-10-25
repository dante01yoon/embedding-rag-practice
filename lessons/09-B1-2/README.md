# 09. 데이터 정제

> B1 · 도서 추천 앱 · 수업 9 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 가짜 값은 빈 칸으로, 틀 조각은 앞에서 잘라 내고, 소개 글이 없거나 20어절이 안 되는 책은 뺐어요. 그리고 책 번호를 붙여 글 파일로 저장했어요.
- 실수 두 개도 기억해 두세요. 기호만 지우면 찌꺼기가 남는다, 그리고 글 파일을 to_csv로 쓰면 따옴표가 붙는다. 저장한 파일은 꼭 열어 보세요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b1/clean.py`](../../b1/clean.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`books/tagged_description.txt`](../../books/tagged_description.txt) | 수업에서 열어 보는 파일 |

읽는 데이터: [`books/books_ko_raw.csv`](../../books/books_ko_raw.csv) · [`books/books_clean.csv`](../../books/books_clean.csv) · [`books/tagged_description.txt`](../../books/tagged_description.txt)

## 실행

```bash
uv run python b1/clean.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

기준을 10어절과 30어절로 바꾸면 몇 권이 남는지 한 줄로 세어 보세요. 그리고 30어절 근처의 소개 글도 몇 개 직접 읽어 보세요.

## 풀이

<details><summary>풀이 보기</summary>

20어절로 거르기 바로 앞 줄에, 10, 20, 30 각각에 대해 기준 이상인 책 수를 세는 한 줄을 넣어요.
10어절이면 1,525권, 20어절이면 1,307권, 30어절이면 1,060권이에요. 30으로 올리면 250권 가까이 더 빠져요. 많이 남기는 것과 내용이 담긴 글만 남기는 것 사이에서 고르는 거예요.

영상에서 입력한 그대로입니다.

- `b1/clean.py`를 엽니다.
- 14행으로 갑니다.

```python
print({n: int((books["words"] >= n).sum()) for n in [10, 20, 30]})
```

- 실행: `uv run python b1/clean.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
