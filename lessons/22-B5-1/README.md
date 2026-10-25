# 22. 골든셋 만들기: LLM이 쓰고 사람이 검수

> B5 · 평가 · 수업 22 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 골든셋은 LLM이 쓰고 사람이 검수하면 빨리 만들 수 있어요. 검수에서는 답이 있는지, 물을 법한지, 베끼지 않았는지 봐요.
- LLM은 매번 다르게 쓰니 한 번 만든 파일을 고정하고, 실제로 막혔던 질문과 사용자 질문을 섞어요.
- 이유도 같이 기억해 두세요. 같은 시험지로 재야 고친 효과를 비교할 수 있고, LLM 질문은 원문 단어를 닮아서 키워드 검색에 유리해요. 그래서 실제 사용자 질문과 답 없는 질문을 섞고, 파일을 다시 만들면 검수도 다시 해요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b5/evaluate.py`](../../b5/evaluate.py) | 수업에서 실행하는 코드 |
| [`b5/make_qa.py`](../../b5/make_qa.py) | 수업 영상에서 빈 파일부터 입력하는 코드 · **OpenRouter 키 필요** (실행할 때마다 LLM 호출) |
| [`b5/review.py`](../../b5/review.py) | 수업 영상에서 빈 파일부터 입력하는 코드 |
| [`k8s/qa_ko.jsonl`](../../k8s/qa_ko.jsonl) | 수업에서 열어 보는 파일 |
| [`b5/load_en.py`](../../b5/load_en.py) | 쿠버네티스 영어 문서를 읽어 k8s/docs_en.json으로 정리 |

읽는 데이터: [`/`](../../) · [`k8s/ko/workloads/controllers/deployment.md`](../../k8s/ko/workloads/controllers/deployment.md) · [`k8s/en/`](../../k8s/en) · [`k8s/docs_en.json`](../../k8s/docs_en.json)

## 실행

```bash
uv run python b5/make_qa.py
uv run python b5/review.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

쿠버네티스를 쓰다가 궁금했던 질문을 직접 써서 HAND에 넣어 보세요. 정답 문서도 직접 찾아서요. 그리고 검색 점수가 어떻게 바뀌는지 보세요.

## 풀이

<details><summary>풀이 보기</summary>

HAND에 컨테이너 로그는 어디에 남고 어떻게 보나요를 더하고, 정답 문서는 로깅 문서로 적어요. 검수 코드를 돌리면 40개가 돼요.
다음 수업에서 만들 평가 코드를 미리 돌려 보면, 한국어 질문이 40개가 됐고, 키워드 검색의 Recall@4가 0.87에서 0.88로 조금 올랐어요. 질문 하나가 점수를 움직여요. 그래서 질문은 많을수록, 다양할수록 좋아요.

영상에서 입력한 그대로입니다.

- `b5/review.py`를 엽니다.
- 9행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
HAND = {"ko": [{"question": "디플로이먼트를 이전 버전으로 되돌리려면 어떻게 하나요?", "path": "k8s/ko/workloads/controllers/deployment.md"},
                {"question": "컨테이너 로그는 어디에 남고 어떻게 보나요?", "path": "k8s/ko/cluster-administration/logging.md"}], "en": []}[LANG]
```

- 실행: `uv run python b5/review.py`
- 실행: `uv run python b5/evaluate.py`

</details>

## 프롬프트

이 수업 코드가 LLM에 보내는 프롬프트 원문입니다. `{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

**[`b5/make_qa.py`](../../b5/make_qa.py#L20) 20행**

```python
"아래 글만 읽고 답할 수 있는 질문을 하나 만드세요. 쿠버네티스를 쓰는 사람이 실제로 물어볼 법한 말투로, 글의 문장을 그대로 베끼지 말고 한 문장으로. 질문만 출력하세요."
```

**[`b5/make_qa.py`](../../b5/make_qa.py#L21) 21행**

```python
"Write one question that can be answered only from the text below. Phrase it the way a real Kubernetes user would ask, in one sentence, without copying sentences from the text. Output only the question."
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
