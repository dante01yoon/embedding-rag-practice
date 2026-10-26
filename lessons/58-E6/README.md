# 58. 현업 사례 · 실시간 추천 — 방금 누른 것까지

> PART E · 실무 사례 해부 · 수업 58 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 실시간 추천은 미리 계산한 아이템 벡터에, 방금 누른 것을 섞은 사용자 벡터로 찾아요. 섞으니 1퍼센트에서 23퍼센트가 됐어요.
- 조건이 붙으면 사후 필터는 추천을 비울 수 있어요. 먼저 좁히고 찾는 사전 필터로 38개 빈 세션이 0개가 됐어요.

## 파일

| 파일 | 설명 |
|---|---|
| [`e6/rec.py`](../../e6/rec.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

읽는 데이터: [`books/books_clean.csv`](../../books/books_clean.csv)

## 실행

```bash
uv run python e6/rec.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

사례처럼, 섞은 벡터 하나로 찾는 대신 예전 취향과 방금 누른 책마다 따로 찾고 RRF로 합치면 어떻게 될까요?

## 풀이

<details><summary>풀이 보기</summary>

rrf_rec은 예전 취향 벡터와 방금 누른 책 두 권의 벡터로 세 번 찾아요. 각 순위에서 받은 점수를 더해 다시 줄 세워요.
Hit@10은 15퍼센트예요. 0.8로 섞은 23퍼센트보다 낮아요.
RRF는 세 목록에 같은 표를 줘요. 예전 취향 한 표, 방금 누른 책 두 표라서, 방금 누른 것의 비중이 3분의 2쯤이에요. 합치는 방식이 곧 비중을 정해요. 사례에서 RRF를 쓴 이유는 정확도보다 요청 수를 줄이는 데 있었어요.

영상에서 입력한 그대로입니다.

- `e6/rec.py`를 엽니다.
- 45행으로 갑니다.

```python

def rrf_rec(old, recent, k=10):  # 사례처럼: 취향 벡터·누른 책마다 따로 찾고 순위를 RRF로 합친다
    s = {}
    for v in [unit(vecs[old].mean(0))] + [vecs[i] for i in recent]:
        sc = vecs @ v
        sc[old + recent] = -9
        for r, i in enumerate(np.argsort(-sc)[:100]):
            s[i] = s.get(i, 0) + 1 / (60 + r + 1)
    return sorted(s, key=s.get, reverse=True)[:k]

hit = np.mean([nxt in rrf_rec(old, recent) for old, recent, nxt in sessions])
print(f"따로 찾고 RRF | 다음 클릭 Hit@10 {hit * 100:4.1f}%")
```

- 실행: `uv run python e6/rec.py`

</details>

📝 이 섹션 퀴즈: [퀴즈 · PART E · 실무 사례 해부](../../quizzes/11-part-e.md)

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
