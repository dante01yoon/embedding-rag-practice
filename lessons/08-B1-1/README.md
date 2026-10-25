# 08. 만들 앱 미리보기와 데이터 살펴보기

> B1 · 도서 추천 앱 · 수업 8 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 모델을 돌리기 전에 데이터를 먼저 열어 봤어요. shape와 head로 모양과 내용, isna와 sum으로 빈 칸, value_counts로 이상한 값, 히스토그램으로 길이를 봤어요.
- 숫자만 세면 놓치는 문제가 있어요. 값찾기처럼요. 그래서 꼭 직접 열어 봐요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b1/explore.png`](../../b1/explore.png) | 수업에서 열어 보는 파일 |
| [`b1/explore.py`](../../b1/explore.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

읽는 데이터: [`books/books_ko_raw.csv`](../../books/books_ko_raw.csv) · [`b1/explore.png`](../../b1/explore.png)

## 실행

```bash
uv run python b1/explore.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

저자 열에서 가장 많은 값 다섯 개를 출력해 보세요. 장르에서 쓴 코드를 한 단어만 바꾸면 돼요. 먼저 직접 해 본 다음에 풀이 영상을 보세요.

## 풀이

<details><summary>풀이 보기</summary>

맨 아래에 장르 대신 저자를 넣은 줄을 하나 더해요.
저자 1등도 값찾기예요. 32권이에요. 장르와 같은 문제가 저자 칸에도 있었어요. 다음 수업에서 같이 고쳐요.

영상에서 입력한 그대로입니다.

- `b1/explore.py`를 엽니다.
- 파일 맨 끝으로 갑니다.

```python
print(books["author"].value_counts().head(5))
```

- 실행: `uv run python b1/explore.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
