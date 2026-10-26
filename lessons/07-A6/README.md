# 07. 검색이 잘 됐는지 재는 법

> PART A · 기초 개념 · 수업 7 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 검색이 좋아졌는지는 골든셋과 지표로 재요.
- Precision과 Recall은 개수, MRR은 첫 정답의 위치, nDCG는 정답들의 위치를 봐요. 그리고 골든셋이 틀릴 수 있다는 점도 같이 봐야 해요.
- 공식을 코드로 옮길 때는 손으로 푼 작은 예와 맞춰 보세요. 등수를 0부터 세는 실수를 바로 잡을 수 있어요.

## 파일

| 파일 | 설명 |
|---|---|
| [`a6/metrics.py`](../../a6/metrics.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`a6/unjudged.py`](../../a6/unjudged.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

읽는 데이터: [`vectors/docids_ko.json`](../../vectors/docids_ko.json) · [`vectors/queries_ko.tsv`](../../vectors/queries_ko.tsv) · [`vectors/qrels_ko.tsv`](../../vectors/qrels_ko.tsv) · [`/`](../../)

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python tools/miracl_vectors.py
```

수업 명령:

```bash
uv run python a6/metrics.py
uv run python a6/unjudged.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

작은 예에서 정답 나와 라를 1등과 2등으로 올려 보세요. 네 지표가 어떻게 바뀔지 먼저 손으로 계산한 다음 코드로 확인해 보세요.

## 풀이

<details><summary>풀이 보기</summary>

ranked 목록 맨 앞에 나와 라를 놓고 실행해요.
Precision 0.4와 Recall 0.67은 그대로예요. 정답 개수가 같으니까요. MRR은 1, nDCG는 0.77로 올랐어요. 순서를 보는 지표만 바뀌었어요.

영상에서 입력한 그대로입니다.

- `a6/metrics.py`를 엽니다.
- 15행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
ranked, rel = ["나", "라", "가", "다", "마"], {"나", "라", "자"}
```

- 실행: `uv run python a6/metrics.py`

</details>

📝 이 섹션 퀴즈: [퀴즈 · PART A · 기초 개념](../../quizzes/01-part-a.md)

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
