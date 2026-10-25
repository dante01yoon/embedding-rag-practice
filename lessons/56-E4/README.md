# 56. 사례 · Uber QueryGPT — 표가 많을 때 텍스트→SQL

> PART E · 실무 사례 해부 · 수업 56 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 표가 많으면 표 이름만 보여 주고 필요한 표를 먼저 고르게 해요. 같은 12개를 맞히면서 입력은 2,732토큰에서 711토큰이 됐어요.
- 그리고 LLM의 답에서 SQL만 꺼내고, 비교 기준을 정해야 채점이 맞아요.
- 범위를 줄이는 이유는 스키마가 다 안 들어가고, 들어가도 헷갈려서예요. 틀리면 뒤가 다 틀리는 표 고르기엔 사람 확인을 둬요.

## 파일

| 파일 | 설명 |
|---|---|
| [`e4/querygpt.py`](../../e4/querygpt.py) | 수업 영상에서 빈 파일부터 입력하는 코드 · **OpenRouter 키 필요** (LLM 답 캐시가 들어 있어 영상과 같은 질문은 추가 비용 없이 재현) |

읽는 데이터: [`chinook/llm_cache_e4.json`](../../chinook/llm_cache_e4.json) · [`chinook/chinook.sqlite`](../../chinook/chinook.sqlite)

## 실행

```bash
uv run python e4/querygpt.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

Uber처럼 칸 줄이기까지 더하면, 입력은 얼마나 줄고 정확도는 어떻게 될까요?

## 풀이

<details><summary>풀이 보기</summary>

prune은 고른 표의 칸 이름만 보여 주고 필요한 칸을 고르게 해요. 그 칸만으로 만든 짧은 스키마로 SQL을 써요.
입력은 질문당 408토큰으로 더 줄었어요. 그런데 12개 중 11개로 하나가 틀렸어요. 브라질 고객 수 질문이에요.
칸을 줄이니 Country 칸 하나만 남았고, LLM은 그 칸에 영어로 Brazil이라고 들어 있는지 몰라서 한글로 브라질이라고 썼어요. 텍스트→SQL 수업의 예시 값 문제예요. 칸을 줄일 때는 그 칸의 예시 값도 함께 남겨야 해요.

영상에서 입력한 그대로입니다.

- `e4/querygpt.py`를 엽니다.
- 61행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
        if name == "표 + 칸 고르기":
            small, t3 = prune(q, tables)
            sql, t2 = to_sql_from(q, small)
            t1 += t3
        else:
            sql, t2 = to_sql(q, tables)
```

- 57행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

````python
def prune(q, tables):  # 칸 고르기: 고른 표의 칸 이름만 보고 필요한 칸만 남긴다
    cols = {t: [r[1] for r in db.execute(f"PRAGMA table_info([{t}])")] for t in tables}
    ans, tok = ask("표와 칸: " + "; ".join(f"{t}({', '.join(c)})" for t, c in cols.items()) + f"\n\n질문에 필요한 칸만 표.칸 형식으로 쉼표로 출력하세요. 표를 잇는 키 칸도 포함하세요.\n질문: {q}")
    keep = {t: [c for c in cs if re.search(rf"\b{t}\.{c}\b", ans)] for t, cs in cols.items()}
    return {t: f"CREATE TABLE {t} (" + ", ".join(cs) + ")" for t, cs in keep.items() if cs}, tok

def to_sql_from(q, schemas):  # 줄인 스키마로 SQL
    sql, tok = ask("SQLite 표:\n" + "\n".join(schemas.values()) + f"\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}")
    m = re.search(r"(SELECT|WITH)\b.*", sql, re.S | re.I)
    return re.sub(r"```", "", m.group(0) if m else sql).strip(), tok

for name in ["표 전부", "표 고르기", "표 + 칸 고르기"]:
````

- 실행: `uv run python e4/querygpt.py`

</details>

## 프롬프트

이 수업 코드가 LLM에 보내는 프롬프트 원문입니다. `{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

**[`e4/querygpt.py`](../../e4/querygpt.py#L39) 39행**

```python
"SQLite 표:\n" + "\n\n".join(SCHEMA[t] for t in tables) + f"\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}"
```

**[`e4/querygpt.py`](../../e4/querygpt.py#L45) 45행**

```python
"데이터베이스 표 이름: " + ", ".join(SCHEMA) + f"\n\n아래 질문에 답하는 데 필요한 표 이름만 쉼표로 출력하세요.\n질문: {q}"
```

**풀이에서 추가**

```python
ans, tok = ask("표와 칸: " + "; ".join(f"{t}({', '.join(c)})" for t, c in cols.items()) + f"\n\n질문에 필요한 칸만 표.칸 형식으로 쉼표로 출력하세요. 표를 잇는 키 칸도 포함하세요.\n질문: {q}")
```

**풀이에서 추가**

```python
sql, tok = ask("SQLite 표:\n" + "\n".join(schemas.values()) + f"\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}")
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
