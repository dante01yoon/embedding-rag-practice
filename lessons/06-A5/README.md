# 06. 근사 이웃 탐색

> PART A · 기초 개념 · 수업 6 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 정확 탐색은 확실하지만 문서 수만큼 느려져요.
- IVF는 가까운 구역만, HNSW는 층이 있는 그래프를 따라 찾고, 양자화는 벡터를 줄여 메모리를 아껴요. 셋 다 정확도를 조금 내주고 속도나 메모리를 얻어요.
- 그리고 오늘 겪은 실수도 기억해 두세요. IVF와 양자화는 add 전에 train이 먼저예요.

## 파일

| 파일 | 설명 |
|---|---|
| [`a5/ann.py`](../../a5/ann.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`a5/tradeoff.py`](../../a5/tradeoff.py) | 수업에서 실행하는 코드 |
| [`a5/concepts.py`](../../a5/concepts.py) | 개념 그림에 쓴 실측값 계산 (정확 탐색 비용 · IVF 구역 크기 · HNSW) |

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python tools/miracl_vectors.py
```

수업 명령:

```bash
uv run python a5/ann.py
uv run python a5/tradeoff.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

nprobe를 64로 올리면 재현율과 시간이 어떻게 되는지, HNSW의 32를 8로 줄이면 어떻게 되는지 재 보세요.

## 풀이

<details><summary>풀이 보기</summary>

nprobe 목록에 64를 더하고, HNSW의 이웃 수를 32에서 8로 바꿔서 다시 실행해요.
nprobe 64는 재현율 0.99지만, 시간이 0.74밀리초로 정확 탐색 0.75와 거의 같아요. HNSW는 이웃을 8개로 줄이니 0.05밀리초로 빨라졌지만, 재현율이 0.94로 떨어졌어요.

영상에서 입력한 그대로입니다.

- `a5/ann.py`를 엽니다.
- 29행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
for nprobe in (1, 8, 32, 64):
```

- 34행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
hnsw = faiss.IndexHNSWFlat(1024, 8, faiss.METRIC_INNER_PRODUCT)  # HNSW: 문서마다 이웃 8개
```

- 실행: `uv run python a5/ann.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
