# 49. 서비스로 나누기 — API · 저장소 · 캐시

> PART D · 운영 · 수업 49 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- API, 저장소, 캐시로 나누고 docker compose로 함께 띄워요. 상자를 바꿀 때마다 같은 성적표로 다시 재요.
- 캐시 키에는 답을 바꾸는 것을 모두 넣고, 캐시 히트율을 지켜봐요.
- 왜 나눴는지도 기억해요. 데이터는 저장소에 남아서 껐다 켜도 그대로고, API는 상태가 없어서 몇 대든 늘릴 수 있고, 가장 비싼 LLM 호출은 캐시로 건너뛰어요.

## 파일

| 파일 | 설명 |
|---|---|
| [`d6/api.py`](../../d6/api.py) | 수업 영상에서 빈 파일부터 입력하는 코드 · **OpenRouter 키 필요** (실행할 때마다 LLM 호출) |
| [`d6/ask.sh`](../../d6/ask.sh) | 질문 하나를 API에 보내 답과 캐시 여부 보기 |
| [`d6/bench.py`](../../d6/bench.py) | API에 골든셋 78개를 두 번 보내 지연 · 비용 · 캐시 효과 재기 |
| [`d6/compose.yaml`](../../d6/compose.yaml) | API · PostgreSQL · Redis를 함께 띄우는 docker compose 파일 |
| [`d6/load.py`](../../d6/load.py) | 청크와 벡터를 PostgreSQL(pgvector)에 넣기 |
| [`d6/update.py`](../../d6/update.py) | 수업에서 실행하는 코드 — 오늘 바뀐 문서 (연습용): 컨피그맵 한도 1MiB → 2MiB. DB의 청크를 바꾸고 벡터도 다시 만든다. |
| [`d6/Dockerfile`](../../d6/Dockerfile) | API 서비스 이미지 |
| [`d6/bench_alert.py`](../../d6/bench_alert.py) | 캐시 히트율이 떨어지면 알림 (KEY_CHANGE=1로 캐시 키가 바뀐 상황 연습) |

읽는 데이터: [`k8s/qa_ko_reviewed.json`](../../k8s/qa_ko_reviewed.json) · [`k8s/qa_ko_short.json`](../../k8s/qa_ko_short.json) · [`k8s/docs_ko.json`](../../k8s/docs_ko.json)

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python b5/evaluate.py
```

수업 명령:

```bash
docker compose -p ragd6 -f d6/compose.yaml up -d --wait
uv run python d6/load.py
zsh d6/ask.sh "컨피그맵에 저장할 수 있는 데이터 한도는?"
uv run python d6/bench.py
uv run python d6/update.py
docker compose -p ragd6 -f d6/compose.yaml up -d --wait --force-recreate api
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

같은 질문인데 캐시 히트율이 갑자기 떨어지면 알림을 내 보세요. 일부러 캐시 키를 바꿔서 시험해 보세요.

## 풀이

<details><summary>풀이 보기</summary>

같은 질문을 다시 보낼 때 히트율이 50퍼센트보다 낮으면 알림을 출력해요. KEY_CHANGE를 켜면 그사이에 색인 버전을 올려서, 모델이나 프롬프트를 바꾼 것처럼 캐시 키를 바꿔요.
첫 번째 다음에 같은 질문을 다시 보냈는데, 캐시 히트율이 0퍼센트예요. 질문당 비용도 0.00035달러로 처음과 같고, 알림이 찍혔어요.
에러가 없어도 비용은 오르고 있었던 거예요. 히트율 알림 한 줄이면 현업 사례처럼 5일 동안 모르는 일을 막을 수 있어요.

영상에서 입력한 그대로입니다.

- `d6/bench.py`를 엽니다.
- 16행으로 갑니다.

```python

    if run == "같은 질문 다시" and hit < ALERT:
        print(f"  알림: 같은 질문인데 캐시 히트율 {hit:.0%} < {ALERT:.0%} · 에러는 없고 비용만 든다 → 캐시 키가 바뀌었는지 확인")
```

- 11행으로 갑니다.

```python
    if run == "같은 질문 다시" and os.environ.get("KEY_CHANGE"):  # 연습: 그사이 캐시 키가 바뀌었다 (모델·프롬프트·색인 교체처럼)
        cache.incr("index:version")
```

- 9행으로 갑니다.

```python
cache = redis.Redis(port=6380)
```

- 8행으로 갑니다.

```python
ALERT = 0.5  # 같은 질문인데 히트율이 이보다 낮으면 알림
```

- 5행으로 갑니다.

```python
import redis
```

- 2행으로 갑니다.

```python
import os
```

- 실행: `KEY_CHANGE=1 uv run python d6/bench.py`

</details>

## 프롬프트

이 수업 코드가 LLM에 보내는 프롬프트 원문입니다. `{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

**[`d6/api.py`](../../d6/api.py#L19) 19행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
