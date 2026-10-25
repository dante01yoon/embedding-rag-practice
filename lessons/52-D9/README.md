# 52. 수집 자동화 — 바뀐 문서를 알아서 색인에

> PART D · 운영 · 수업 52 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 수집 파이프라인은 정해진 시간에 바뀐 문서를 찾고, 파싱하고, 청킹하고, 바뀐 청크만 임베딩해서 색인에 넣고, 처리 건수를 보고해요.
- 바뀐 문서는 수정 시각만 믿지 말고 내용 해시로 확인해요. 그리고 다시 돌려도 결과가 같게 만들어요.
- 이유도 기억해요. 수정 시각은 동기화 도구 때문에 거짓말을 할 수 있고, 해시는 싸고, 임베딩은 비싸요. 그리고 예약 작업은 언젠가 두 번 돌고, 언젠가 실패해요. 그래서 해시, 멱등성, 재시도를 갖춰요.

## 파일

| 파일 | 설명 |
|---|---|
| [`d9/ingest.py`](../../d9/ingest.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`d9/upstream.py`](../../d9/upstream.py) | 오늘 바뀐 문서 흉내 (내용만 바뀐 문서 · 새 문서 · 지운 문서) |
| [`d9/ingest_retry.py`](../../d9/ingest_retry.py) | 임베딩이 실패하면 기다렸다 다시 시도하는 수집기 |
| [`d9/setup.py`](../../d9/setup.py) | 수집 실습 준비: d9/docs · 어제까지의 색인 · 상태 파일 만들기 (처음 한 번) |

읽는 데이터: [`k8s/docs_ko.json`](../../k8s/docs_ko.json) · [`k8s/ko/`](../../k8s/ko) · [`/`](../../)

## 실행

먼저 필요한 벡터 파일 (이미 만들었다면 건너뜁니다):

```bash
uv run python d9/setup.py
```

수업 명령:

```bash
uv run python d9/upstream.py
uv run python d9/ingest.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

임베딩 서버가 가끔 응답하지 않으면 어떻게 할까요? 실패하면 잠깐 기다렸다 다시 시도하게 만들고, 일부러 장애를 내서 시험해 보세요.

## 풀이

<details><summary>풀이 보기</summary>

embed가 실패하면 1초, 그다음 2초 기다렸다가 다시 시도하고, 세 번 모두 실패하면 포기해요. 기다리는 시간을 두 배씩 늘리는 이 방식을 지수 백오프라고 해요. CHAOS를 켜면 첫 시도를 일부러 실패시켜요.
점검 공지에 한 줄을 더하고, 장애 연습을 켜고 돌렸어요. 첫 시도가 실패해서 재시도 1이 찍히고, 다시 시도해서 성공했어요. 처리 1, 실패 0이에요.
장애를 일부러 내 보는 건 현업에서도 써요. 재시도 코드는 장애가 나야만 실행되니까, 평소에 시험해 두지 않으면 정작 필요할 때 동작하는지 몰라요.

영상에서 입력한 그대로입니다.

- `d9/ingest.py`를 엽니다.
- 22행으로 갑니다.
- 그 자리의 줄 2개를 지웁니다.

```python
def embed(texts, tries=3):  # 실패하면 1초, 2초 기다렸다 다시 · 끝내 실패하면 예외
    for n in range(tries):
        try:
            if os.environ.get("CHAOS") and n == 0:  # 장애 연습: 첫 시도를 일부러 실패시킨다
                raise TimeoutError("임베딩 서버 응답 없음")
            return model.encode(texts, normalize_embeddings=True)
        except TimeoutError as e:
            if n == tries - 1:
                raise
            print(f"  재시도 {n + 1} · {e}")
            time.sleep(2 ** n)
```

- 실행: `echo "추가: 점검은 한 시간 걸린다." >> d9/docs/notice__maintenance.md && CHAOS=1 uv run python d9/ingest.py`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
