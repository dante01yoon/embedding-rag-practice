# 51. 배포 전 자동 검사 — 점수가 떨어지면 배포를 막는다

> PART D · 운영 · 수업 51 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 배포 전에 코드 테스트와 골든셋 평가를 자동으로 돌리고, 베이스라인보다 떨어지면 종료 코드 1로 배포를 막아요.
- 베이스라인은 검사가 아니라 사람이 명령으로 바꿔요. 그래야 다시 돌리기로 통과하는 구멍이 없어요.
- 이렇게까지 하는 이유는, RAG는 설정 한 줄로 에러 없이 나빠지기 때문이에요. 사람 눈으로는 놓치니까, 숫자로 재고 숫자로 막아요.

## 파일

| 파일 | 설명 |
|---|---|
| [`d8/gate.py`](../../d8/gate.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`d8/test_chunk.py`](../../d8/test_chunk.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`d8/rag-ci.yml`](../../d8/rag-ci.yml) | GitHub Actions 워크플로 예시. 쓰려면 `.github/workflows/`로 복사합니다 |
| [`d8/settings.json`](../../d8/settings.json) | PR에서 바뀌는 검색 설정 (청크 크기 · 오버랩 · top_k) |

읽는 데이터: [`d8/settings.json`](../../d8/settings.json) · [`k8s/docs_ko.json`](../../k8s/docs_ko.json) · [`k8s/qa_ko_reviewed.json`](../../k8s/qa_ko_reviewed.json) · [`k8s/qa_ko_short.json`](../../k8s/qa_ko_short.json)

## 실행

```bash
uv run pytest -q d8
uv run python d8/gate.py
echo '{"chunk_size": 500, "overlap": 100, "top_k": 2}' > d8/settings.json && cat d8/settings.json
echo '{"chunk_size": 500, "overlap": 100, "top_k": 4}' > d8/settings.json && uv run python d8/gate.py --update
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

이 검사를 GitHub에서 PR마다 자동으로 돌리고, 통과했을 때만 배포되게 설정 파일을 써 보세요.

## 풀이

<details><summary>풀이 보기</summary>

GitHub Actions 설정 파일이에요. check 작업이 코드 테스트와 골든셋 검사를 돌리고, deploy 작업은 needs로 check가 통과해야만 실행돼요. main에 합쳐질 때만 배포해요.
확대해서 볼게요. 맨 위에는 언제 돌지 적어요. 코드를 올릴 때와 PR을 열 때예요. check 작업은 우분투 컴퓨터를 빌려서 코드를 받고, uv로 설치하고, 코드 테스트와 골든셋 검사를 차례로 돌려요. 한 줄이라도 종료 코드가 0이 아니면 거기서 멈춰요.
deploy 작업은 needs에 check가 있어서, check가 통과해야만 시작해요. if는 main 브랜치에 합쳐졌을 때만 배포하라는 조건이에요. 그래서 PR 단계에서는 검사만 하고 배포는 하지 않아요.
같은 명령을 내 컴퓨터에서 차례로 돌려 봤어요. 테스트는 통과했지만 골든셋 검사가 실패해서, 마지막의 배포 진행은 찍히지 않았어요. GitHub에서는 이게 배포 작업이 실행되지 않는 것으로 보여요.
실제로 GitHub에서 돌릴 때는 임베딩 모델을 내려받는 데 몇 분이 걸려요. 모델과 벡터 파일을 캐시해 두면 빨라져요.

영상에서 입력한 그대로입니다.

- `.github/workflows/rag-ci.yml`를 엽니다. (이 저장소에서는 `d8/rag-ci.yml`을 이 자리로 복사해서 씁니다)

```
name: rag-ci
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run pytest -q d8  # 1) 코드 테스트
      - run: uv run python d8/gate.py  # 2) 골든셋 평가 · 베이스라인보다 떨어지면 실패
  deploy:
    needs: check  # check가 통과해야만 실행된다
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "여기에 배포 명령"
```

- 실행: `uv run pytest -q d8 && uv run python d8/gate.py && echo "배포 진행"`

</details>

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
