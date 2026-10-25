# 10. 벡터 DB에 넣고 문장으로 찾기

> B1 · 도서 추천 앱 · 수업 10 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 단어로 찾으면 흔한 단어에 끌리고, 뜻이 같아도 단어가 다르면 놓쳐요. 그래서 문장을 벡터로 바꿔 가까운 점을 찾았어요.
- 그리고 벡터 DB는 벡터를 저장하고, 빠르게 찾고, 원문과 id를 함께 보관해요. id를 꼭 정해서 넣어야 다시 실행해도 중복이 생기지 않아요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b1/vector.py`](../../b1/vector.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

읽는 데이터: [`books/books_clean.csv`](../../books/books_clean.csv) · [`books/tagged_description.txt`](../../books/tagged_description.txt)

## 실행

```bash
uv run python b1/vector.py
rm -rf books/chroma
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

우주를 여행하는 SF 모험을 세 권만 추천받아 보세요. recommend에 k를 3으로 주면 돼요. 먼저 직접 해 본 다음에 풀이 영상을 보세요.

## 풀이

<details><summary>풀이 보기</summary>

맨 아래에 print 한 줄을 더하고, k에 3을 넣어요. 그리고 실행해요.
히페리온, 우주복 있음 출장 가능, 은하수를 여행하는 히치하이커를 위한 안내서가 나왔어요. 셋 다 우주가 배경인 SF 소설이에요.

영상에서 입력한 그대로입니다.

- `b1/vector.py`를 엽니다.
- 파일 맨 끝으로 갑니다.

```python
print(recommend("우주를 여행하는 SF 모험", k=3))
```

- 실행: `uv run python b1/vector.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
