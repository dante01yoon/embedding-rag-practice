# 20. LangChain으로 다시 만들기

> B4 · 프레임워크와 화면 · 수업 20 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- 직접 만든 부분마다 LangChain 부품이 있어요. 리트리버, 프롬프트 템플릿, 채팅 모델, 출력 파서예요. 번호 붙이기는 그대로 가져갔어요.
- LCEL의 세로 막대는 앞 결과를 다음으로 넘기고, 맨 앞의 사전은 질문 하나로 여러 칸을 채워요. 그래서 invoke에는 질문 글자 하나만 넣어요.
- 이유도 같이 기억해 두세요. 모든 부품이 invoke라는 같은 손잡이를 가져서 갈아 끼우기 쉬워요. 그 대신 기본값과 오류가 블록 안에 숨어요. 그래서 결과를 바꾸는 값은 직접 적어 두고, 이상하면 블록 안을 열어 봐요.

## 파일

| 파일 | 설명 |
|---|---|
| [`b4/chain.py`](../../b4/chain.py) | 수업 영상에서 빈 파일부터 입력하는 코드 · **OpenRouter 키 필요** (실행할 때마다 LLM 호출) |

읽는 데이터: [`k8s/docs_ko.json`](../../k8s/docs_ko.json)

## 실행

```bash
uv run python b4/chain.py
```

저장소 맨 위 폴더에서 실행합니다. 처음이라면 [벡터 파일 만들기](../../README.md#벡터-파일-만들기)를 먼저 확인하세요.

## 과제

청크 크기를 500에서 200으로, 오버랩을 0으로 바꾸고 다시 실행해 보세요. 출처가 어떻게 바뀌는지 보세요.

## 풀이

<details><summary>풀이 보기</summary>

자르기 줄의 chunk_size를 200, chunk_overlap을 0으로 바꾸고 실행해요.
그런데 출처가 하나도 안 바뀌었어요. 인그레스 두 개, 서비스 두 개 그대로예요. 왜 그럴까요?
그래서 폴더 이름을 크기마다 다르게 해요. 세 군데의 chroma_lc를 chroma_lc200으로 바꿔요. 새 폴더니까 처음부터 다시 색인해요.
이제야 출처 순서와 구성이 바뀌었어요. 그리고 답 끝을 보세요. 아까는 NodePort와 LoadBalancer를 둘 다 말했는데, 이번엔 NodePort 하나만 남았어요. 200자 청크라 문장이 잘려서 한쪽만 들어온 거예요. 청킹 수업의 저울질이 그대로 보여요.
그리고 꼭 기억할 것. 설정을 바꿨는데 결과가 그대로라면, 그 설정이 정말 쓰였는지부터 의심해 보세요. 현업에서도 아주 흔한 실수예요.

영상에서 입력한 그대로입니다.

- `b4/chain.py`를 엽니다.
- 20행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
    chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0).split_documents(docs)  # 청킹
```

- 실행: `uv run python b4/chain.py`
- 18행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
if not os.path.exists("k8s/chroma_lc200"):  # 처음 한 번만 색인한다
```

- 21행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
    Chroma.from_documents(chunks, embed, persist_directory="k8s/chroma_lc200")  # 벡터로 바꿔 저장
```

- 22행으로 갑니다.
- 그 자리의 줄 1개를 지웁니다.

```python
retriever = Chroma(persist_directory="k8s/chroma_lc200", embedding_function=embed).as_retriever(search_kwargs={"k": 4})
```

- 실행: `uv run python b4/chain.py`

</details>

## 프롬프트

이 수업 코드가 LLM에 보내는 프롬프트 원문입니다. `{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

**[`b4/chain.py`](../../b4/chain.py#L25) 25행**

```python
"아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 없으면 모른다고 답하세요.\n\n{context}\n\n질문: {question}"
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
