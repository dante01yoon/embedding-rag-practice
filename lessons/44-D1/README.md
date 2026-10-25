# 44. API로 띄우고 · 지연과 비용 재기

> PART D · 운영 · 수업 44 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- RAG를 FastAPI로 감싸고, 질문을 보내 p50, p95, 질문당 비용을 쟀어요.
- 요청마다 모델을 읽으면 p95가 73초, 서버가 뜰 때 한 번 읽으면 4.1초였어요. 무거운 준비는 한 번만 해요.
- 이유도 같이 기억해요. 서버에서 함수 밖은 한 번, 안은 요청마다 돌아요. p95는 느린 5퍼센트를 놓치지 않으려고 보고, 비용은 입력과 출력을 나눠 봐야 어디를 줄일지 보여요.

## 파일

| 파일 | 설명 |
|---|---|
| [`d1/api.py`](../../d1/api.py) | 수업 영상에서 빈 파일부터 입력하는 코드 · **OpenRouter 키 필요** (실행할 때마다 LLM 호출) |
| [`d1/bench.py`](../../d1/bench.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |

읽는 데이터: [`k8s/docs_ko.json`](../../k8s/docs_ko.json) · [`k8s/qa_ko_short.json`](../../k8s/qa_ko_short.json)

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python b5/evaluate.py
```

수업 명령:

```bash
uv run python d1/bench.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

같은 질문이 또 오면, 답을 저장해 두었다가 바로 돌려주게 해 보세요. 그리고 지연과 비용이 어떻게 바뀌는지 재 보세요.

## 풀이

<details><summary>풀이 보기</summary>

api.py에 CACHE를 두고, 질문이 있으면 저장한 답을 바로 돌려주고, 토큰 수는 0으로 적어요. bench.py에서는 같은 질문 20개를 한 번 더 보내요.
40개 중 절반이 캐시에서 나와서, p50은 0.69초, 질문당 비용은 절반인 0.00016달러예요.
다만 이 답 캐시에는 큰 함정이 있어요. 다음 수업에서 권한을 다루면서, 이 캐시가 어떻게 비밀을 새게 만드는지 직접 봐요.

영상에서 입력한 그대로입니다.

- `d1/api.py`를 엽니다.
- 23행으로 갑니다.

```python
CACHE = {}  # 같은 질문이면 저장해 둔 답
```

- 28행으로 갑니다.

```python
    if q in CACHE:
        return CACHE[q] | {"in": 0, "out": 0, "search_sec": 0, "llm_sec": 0}
```

- 34행으로 갑니다.
- 그 자리의 줄 2개를 지웁니다.

```python
    CACHE[q] = {"answer": r.choices[0].message.content, "in": r.usage.prompt_tokens, "out": r.usage.completion_tokens,
                "search_sec": round(t1 - t0, 2), "llm_sec": round(time.time() - t1, 2)}
    return CACHE[q]
```

- `d1/bench.py`를 엽니다.
- 12행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
QS = [x["question"] for x in json.load(open("k8s/qa_ko_short.json"))][:20] * 2  # 같은 질문이 한 번 더 온다
```

- 실행: `uv run python d1/bench.py`

</details>

## 프롬프트

이 수업 코드가 LLM에 보내는 프롬프트 원문입니다. `{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

**[`d1/api.py`](../../d1/api.py#L21) 21행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
