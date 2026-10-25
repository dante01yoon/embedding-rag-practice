# 59. 최종 미션 — 지원서에 넣을 RAG 평가 리포트

> 최종 미션 · 수업 59 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 리포트는 검색과 답을 따로, 숫자마다 신뢰구간을 붙여요. 거절처럼 성격이 다른 실패는 따로 세어요.
- 그리고 실패 사례는 원인까지, 지연과 비용은 p95와 하루 비용까지, 데모는 한도를 걸고 공개해요.
- 그리고 이유도 기억해요. 검색과 답을 나누는 건 고칠 곳을 찾기 위해서, 신뢰구간은 그 숫자를 얼마나 믿을지 보여 주기 위해서예요.

## 파일

| 파일 | 설명 |
|---|---|
| [`mission/failures.py`](../../mission/failures.py) | 수업에서 실행하는 코드 |
| [`mission/report.py`](../../mission/report.py) | 수업 영상에서 빈 파일부터 입력하는 코드 · **OpenRouter 키 필요** (실행할 때마다 LLM 호출) |
| [`mission/REPORT.md`](../../mission/REPORT.md) | 최종 미션에서 만든 평가 리포트 예시 |
| [`mission/rows.json`](../../mission/rows.json) | 평가 리포트의 질문별 결과 |

읽는 데이터: [`mission/rows.json`](../../mission/rows.json) · [`k8s/docs_ko.json`](../../k8s/docs_ko.json) · [`k8s/qa_ko_reviewed.json`](../../k8s/qa_ko_reviewed.json) · [`k8s/qa_ko_short.json`](../../k8s/qa_ko_short.json) · [`mission/REPORT.md`](../../mission/REPORT.md)

## 실행

```bash
uv run python mission/report.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

이제 여러분 차례예요. 여러분의 문서로 이 리포트를 만들어 보세요. 그리고 실패 사례를 원인별로 나눠 보세요. 검색이 못 찾은 것, 찾고도 거절한 것, 자료 밖 내용을 쓴 것이요.

## 풀이

<details><summary>풀이 보기</summary>

failures.py는 report.py가 남긴 질문별 기록을 읽어서, 검색 실패, 찾고도 거절, 자료 밖 내용 순서로 원인을 정하고 개수와 예를 하나씩 출력해요.
검색 실패 9개, 찾고도 거절 7개, 자료 밖 내용 4개, 합쳐서 78개 중 20개예요. 고칠 순서가 보여요. 검색이 먼저고, 그다음은 찾고도 거절하는 답이에요.
찾고도 거절한 7개는 자료에 답이 있는데 프롬프트가 너무 조심스러운 경우일 수 있어요. 이렇게 원인을 나누면 다음에 무엇을 고칠지 숫자로 정할 수 있어요.

영상에서 입력한 그대로입니다.

- `mission/failures.py`를 엽니다.

```python
import collections
import json

rows = json.load(open("mission/rows.json"))  # report.py가 남긴 질문별 기록

def cause(r):  # 실패를 원인별로: 검색 → 답 거절 → 자료 밖 내용 순서로 본다
    if not r["hit"]:
        return "검색 실패"
    if r["refused"]:
        return "찾고도 거절"
    if not r["faithful"]:
        return "자료 밖 내용"
    return None

c = collections.Counter(filter(None, map(cause, rows)))
for k, n in c.most_common():
    ex = next(r for r in rows if cause(r) == k)
    print(f"{k:<8} | {n}개 · 예: {ex['q'][:38]}")
print(f"실패 합계 {sum(c.values())}/{len(rows)}")
```

- 실행: `uv run python mission/failures.py`

</details>

## 프롬프트

이 수업 코드가 LLM에 보내는 프롬프트 원문입니다. `{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

**[`mission/report.py`](../../mission/report.py#L22) 22행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`mission/report.py`](../../mission/report.py#L23) 23행**

```python
"자료:\n{ctx}\n\n답:\n{a}\n\n답의 모든 내용이 자료로 뒷받침되면 '예', 자료에 없는 내용이 하나라도 있으면 '아니오'라고만 답하세요."
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
