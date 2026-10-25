# 55. 사례 · LinkedIn 고객 지원 지식 그래프 — 우리 문서에서도 될까

> PART E · 실무 사례 해부 · 수업 55 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- LinkedIn은 티켓을 칸마다 노드로, 티켓 사이를 선으로 이은 지식 그래프로 MRR을 77.6퍼센트 올렸어요.
- 우리 문서에서는 절을 자르는 실수를 고쳐도 0.827로 평평한 청크 0.854에 못 미쳤어요. 사례는 숫자가 아니라 조건까지 옮겨 와야 해요.
- LinkedIn의 방법이 통한 이유는, 칸이 정해진 데이터에서 칸끼리 비교하고 답이 있는 칸을 통째로 꺼냈기 때문이에요.

## 파일

| 파일 | 설명 |
|---|---|
| [`e3/kg.py`](../../e3/kg.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

읽는 데이터: [`k8s/docs_ko.json`](../../k8s/docs_ko.json) · [`k8s/qa_ko_reviewed.json`](../../k8s/qa_ko_reviewed.json) · [`k8s/qa_ko_short.json`](../../k8s/qa_ko_short.json)

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python b5/evaluate.py
```

수업 명령:

```bash
uv run python e3/kg.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

티켓 사이 관계처럼, 문서 사이 링크를 따라 이웃 문서의 점수를 조금 더해 주면 평평한 청크보다 좋아질까요?

## 풀이

<details><summary>풀이 보기</summary>

본문의 링크를 우리 문서 경로로 바꾸고, 문서 점수에 링크된 이웃 중 가장 높은 점수의 0.1배를 더해요.
링크 559개를 따라갔는데, MRR은 0.849예요. 평평한 청크의 0.854와 거의 같고, 조금 낮아요.
문서 링크는 정답을 찾아 주는 관계라기보다, 더 읽을거리를 이어 주는 링크라서예요. 관계 선이 도움이 되려면 그 선이 질문과 맞는 의미를 가져야 해요.

영상에서 입력한 그대로입니다.

- `e3/kg.py`를 엽니다.
- 46행으로 갑니다.

```python

paths = [d["path"] for d in docs]
link = lambda u: next((paths.index(c) for c in [f"k8s/ko/{u}.md", f"k8s/ko/{u}/_index.md"] if c in paths), None)  # noqa: E731
nbr = [{link(re.sub(r"^(/ko)?/docs/concepts/", "", u.split("#")[0].rstrip("/"))) for u in re.findall(r"\]\((/(?:ko/)?docs/[^)\s]+)\)", d["text"])} - {None} for d in docs]
V, owner = np.load("k8s/vecs_ko_500.npy"), np.array([paths.index(p) for p, _ in flat])
got = []
for x in qa:
    best = np.full(len(docs), -1.0)
    np.maximum.at(best, owner, V @ model.encode(x["question"], normalize_embeddings=True))  # 문서마다 가장 가까운 청크 점수
    score = best + 0.1 * np.array([max([best[n] for n in nbr[i]], default=0) for i in range(len(docs))])  # 링크된 이웃의 점수를 조금
    top = list(np.argsort(-score)[:10])
    got.append(1 / (top.index(paths.index(x["path"])) + 1) if paths.index(x["path"]) in top else 0)
print(f"청크 + 링크 이웃 | 링크 {sum(map(len, nbr))}개 · MRR@10 {np.mean(got):.3f}")
```

- 실행: `uv run python e3/kg.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
