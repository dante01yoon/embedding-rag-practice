# 23. 성적표: 키워드 vs 벡터 · 한국어 vs 영어

> B5 · 평가 · 수업 23 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- Recall@4는 정답이 상위 4개 안에 들었나, MRR은 정답이 몇 등인지의 역수예요. 같은 질문으로 키워드와 벡터, 한국어와 영어를 나란히 쟀어요.
- 한국어 키워드 검색은 조사 때문에 약했어요. 성적표의 숫자가 이상하면, 언어의 특징부터 의심해 보세요.
- 이유도 같이 기억해 두세요. 들었는지와 몇 등인지는 다른 정보라서 두 점수를 함께 보고, 청크가 겹치니까 문서 단위로 채점했어요. 한국어는 같은 말이 조사 때문에 여러 서랍으로 흩어지니까, 형태소로 잘라 모아 줘야 해요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b5/evaluate.py`](../../b5/evaluate.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

## 실행

```bash
uv run python b5/evaluate.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

한국어 BM25에 형태소 분석기 Kiwi를 써서, 조사를 떼고 비교하게 바꿔 보세요. 영어는 그대로 띄어쓰기로요. 점수가 어떻게 바뀌는지 보세요.

## 풀이

<details><summary>풀이 보기</summary>

Kiwi를 불러오고, words 함수를 만들어요. 영어는 띄어쓰기로, 한국어는 형태소로 자르고 명사, 동사 같은 뜻 있는 말만 남겨요. 그리고 색인과 검색의 두 군데를 words로 바꿔요.
한국어 BM25가 Recall 0.87에서 0.95로, MRR은 0.77에서 0.94로 올랐어요. MRR은 벡터 검색의 0.90보다도 높아요. 정답을 더 앞쪽에 올린 거예요.
자르는 방법 하나로 키워드 검색이 벡터 검색을 따라잡았어요.

영상에서 입력한 그대로입니다.

- `b5/evaluate.py`를 엽니다.
- 13행으로 갑니다.

```python
from kiwipiepy import Kiwi  # 한국어 형태소 분석기

kiwi = Kiwi()

def words(text, lang):  # 한국어는 형태소로 · 영어는 띄어쓰기로
    if lang == "en":
        return text.lower().split()
    return [t.form for t in kiwi.tokenize(text.lower()) if t.tag[0] in "NVSX" or t.tag.startswith("SL")]

```

- 35행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
    bm.index([words(c, lang) for _, c in chunks], show_progress=False)
```

- 45행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
                idx, _ = bm.retrieve([words(item["question"], lang)], k=10, show_progress=False)
```

- 실행: `uv run python b5/evaluate.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
