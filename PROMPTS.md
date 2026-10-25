# 프롬프트 모음

강의 실습 코드가 LLM에 보내는 프롬프트 원문을 수업 순서대로 모았습니다. 각 수업 폴더의 README에도 같은 내용이 있습니다.
`{...}` 자리에는 실행할 때 질문 · 자료가 들어갑니다.

## [02. LLM, 토큰, 그리고 왜 검색이 필요한가](lessons/02-A1/README.md)

**[`a1/ask.py`](a1/ask.py#L12) 12행**

```python
f"참고 문서:\n{doc}\n\n질문: {question}"
```

## [16. RAG 한눈에 보기](lessons/16-B3-1/README.md)

**[`b3/rag.py`](b3/rag.py#L26) 26행**

```python
f"아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 없으면 모른다고 답하세요.\n\n"
              f"{context}\n\n질문: {question}"
```

## [19. 40줄로 RAG 만들기](lessons/19-B3-4/README.md)

**[`b3/rag.py`](b3/rag.py#L26) 26행**

```python
f"아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 없으면 모른다고 답하세요.\n\n"
              f"{context}\n\n질문: {question}"
```

## [20. LangChain으로 다시 만들기](lessons/20-B4-1/README.md)

**[`b4/chain.py`](b4/chain.py#L25) 25행**

```python
"아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 없으면 모른다고 답하세요.\n\n{context}\n\n질문: {question}"
```

## [22. 골든셋 만들기: LLM이 쓰고 사람이 검수](lessons/22-B5-1/README.md)

**[`b5/make_qa.py`](b5/make_qa.py#L20) 20행**

```python
"아래 글만 읽고 답할 수 있는 질문을 하나 만드세요. 쿠버네티스를 쓰는 사람이 실제로 물어볼 법한 말투로, 글의 문장을 그대로 베끼지 말고 한 문장으로. 질문만 출력하세요."
```

**[`b5/make_qa.py`](b5/make_qa.py#L21) 21행**

```python
"Write one question that can be answered only from the text below. Phrase it the way a real Kubernetes user would ask, in one sentence, without copying sentences from the text. Output only the question."
```

## [26. 질의 변환: 여러 질문 · 가상의 답](lessons/26-B6-3/README.md)

**[`b6/query.py`](b6/query.py#L44) 44행**

```python
f"다음 질문을 같은 뜻의 다른 표현으로 3개 써 주세요. 한 줄에 하나씩, 질문만.\n\n{q}"
```

**[`b6/query.py`](b6/query.py#L49) 49행**

```python
f"다음 질문에 쿠버네티스 문서처럼 짧은 한 문단으로 답해 주세요.\n\n{q}"
```

**풀이에서 추가**

```python
qa = [{**x, "question": ask(f"다음 질문을 사람들이 검색창에 대충 치듯 2~4 단어로 줄여 주세요. 줄인 말만 출력.\n\n{x['question']}")} for x in qa]
```

## [27. 라우팅과 셀프 쿼리](lessons/27-B6-4/README.md)

**[`b6/route.py`](b6/route.py#L31) 31행**

```python
f"다음 질문이 쿠버네티스 문서에 대한 질문이면 k8s, 책 추천 요청이면 books라고 한 단어로만 답하세요.\n\n{q}"
```

**풀이에서 추가**

```python
raw = ask(f"오늘은 {date.today()}입니다. " + SELF + q)
```

## [28. 맥락 검색 (contextual retrieval)](lessons/28-B6-5/README.md)

**[`b6/contextualize.py`](b6/contextualize.py#L18) 18행**

```python
"""<document>
제목: {title}
{head}
</document>
다음은 위 문서에서 잘라 낸 청크입니다.
<chunk>
{chunk}
</chunk>
검색이 잘 되도록, 이 청크가 문서 안에서 무엇에 대한 내용인지 한두 문장으로 짧게 설명하세요. 설명만 출력하세요."""
```

## [29. 청킹 방법 다섯 가지 · 공정하게 비교하기](lessons/29-B6-6/README.md)

**[`b3x/agentic.py`](b3x/agentic.py#L27) 27행**

```python
"아래는 번호를 붙인 문서의 문장들입니다. 주제가 바뀌는 곳에서 묶음을 나누세요. 한 묶음은 대략 300~900자입니다.\n"
          "각 묶음이 시작하는 문장 번호만 쉼표로 출력하세요. 예: 0, 7, 15\n\n{body}"
```

**[`b3x/make_qa.py`](b3x/make_qa.py#L17) 17행**

```python
"아래 문장 하나로 답할 수 있는 짧은 질문을 한국어로 하나만 쓰세요. 문장의 표현을 그대로 베끼지 말고, 사용자가 실제로 물을 법한 말로 쓰세요. 질문만 출력하세요.\n\n문장: {s}"
```

## [30. 에이전트 청킹 · LLM이 읽고 경계를 정하면](lessons/30-B6-7/README.md)

**[`b3x/agent_cut.py`](b3x/agent_cut.py#L35) 35행**

```python
"아래는 번호를 붙인 문서의 문장들입니다. 주제가 바뀌는 곳에서 묶음을 나누세요. 한 묶음은 대략 {size}자입니다.\n각 묶음이 시작하는 문장 번호만 쉼표로 출력하세요. 예: 0, 7, 15\n\n{body}"
```

## [31. 근거만 쓰게 하기와 거절](lessons/31-B7-1/README.md)

**[`b7/answer.py`](b7/answer.py#L38) 38행**

```python
"아래 자료를 참고해 질문에 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`b7/answer.py`](b7/answer.py#L39) 39행**

```python
"아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 답이 없으면 '" + NOANS + "'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [32. LLM 심판: 근거 충실도 채점과 심판 검증](lessons/32-B7-2/README.md)

**[`b7/judge.py`](b7/judge.py#L41) 41행**

```python
"아래 자료와 답을 비교하세요. 답의 문장 중 하나라도 자료로 확인되지 않으면 '근거 없음', 모두 확인되면 '충실'이라고만 답하세요.\n\n자료:\n{ctx}\n\n답: {a}"
```

## [33. LangGraph로 스스로 고치는 RAG (CRAG)](lessons/33-B8-1/README.md)

**[`b8/crag.py`](b8/crag.py#L46) 46행**

```python
f"질문: {s['question']}\n\n자료: {chunks[i][2]}\n\n이 자료가 질문에 답하는 데 도움이 되면 '예', 아니면 '아니오'라고만 답하세요."
```

**[`b8/crag.py`](b8/crag.py#L51) 51행**

```python
f"다음 질문을 쿠버네티스 공식 문서에서 찾기 좋은 검색 문장 하나로 다시 써 주세요. 검색 문장만 출력하세요.\n\n{s['question']}"
```

**[`b8/crag.py`](b8/crag.py#L56) 56행**

```python
f"아래 자료만 보고 답하세요. 자료에 답이 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {s['question']}"
```

**풀이에서 추가**

```python
keep = [i for i in s["found"] if ask(f"질문: {s['question']}\n\n자료: {chunks[i][2]}\n\n이 자료가 질문과 조금이라도 관련이 있으면 '예', 전혀 관계없으면 '아니오'라고만 답하세요.").startswith("예")]
```

## [34. Adaptive RAG: 질문의 종류를 보고 길 고르기](lessons/34-B8-2/README.md)

**[`b8/adaptive.py`](b8/adaptive.py#L37) 37행**

```python
f"다음 인사나 잡담에 한 문장으로 친절하게 답하고, 쿠버네티스 질문은 편하게 하라고 덧붙이세요.\n\n{s['question']}"
```

**[`b8/crag.py`](b8/crag.py#L46) 46행**

```python
f"질문: {s['question']}\n\n자료: {chunks[i][2]}\n\n이 자료가 질문에 답하는 데 도움이 되면 '예', 아니면 '아니오'라고만 답하세요."
```

**[`b8/crag.py`](b8/crag.py#L51) 51행**

```python
f"다음 질문을 쿠버네티스 공식 문서에서 찾기 좋은 검색 문장 하나로 다시 써 주세요. 검색 문장만 출력하세요.\n\n{s['question']}"
```

**[`b8/crag.py`](b8/crag.py#L56) 56행**

```python
f"아래 자료만 보고 답하세요. 자료에 답이 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {s['question']}"
```

## [35. GraphRAG: 관계를 따라 찾기](lessons/35-B9-1/README.md)

**[`b9/graph.py`](b9/graph.py#L45) 45행**

```python
f"다음 질문에 나오는 작가 이름만 출력하세요.\n\n{q}"
```

**풀이에서 추가**

```python
name = word if any(word in n for n in G if n.startswith("작가:")) else ask(f"다음 질문에 나오는 작가 이름만 출력하세요.\n\n{q}")  # 그래프에 있으면 그대로, 없을 때만 LLM
```

## [36. 표와 그림이 든 PDF · 멀티모달 RAG](lessons/36-B9-2/README.md)

**[`b9/table.py`](b9/table.py#L62) 62행**

```python
f"아래 자료만 보고 금액 하나로 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`b9/table.py`](b9/table.py#L78) 78행**

```python
f"이 쪽 그림만 보고 금액 하나로 답하세요.\n\n질문: {q}"
```

## [38. 긴 자료를 통째로 넣으면? · Lost in the Middle 다시 재기](lessons/38-C1-2/README.md)

**[`c1/middle.py`](c1/middle.py#L40) 40행**

```python
"아래 자료를 보고 질문에 숫자 하나로만 답하세요.\n\n" + "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(ctx)) + f"\n\n질문: {s} 서버의 점검 암호는?"
```

## [39. "전부 몇 개?" 집계 질문](lessons/39-C1-3/README.md)

**[`c1/count.py`](c1/count.py#L34) 34행**

```python
f"아래 도서 목록만 보고 숫자 하나로만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`c1/count.py`](c1/count.py#L44) 44행**

```python
f"다음 질문에 나오는 작가 이름만 출력하세요.\n\n{q}"
```

## [40. 근거 없는 답 · 환각 재고 줄이기](lessons/40-C1-4/README.md)

**[`c1/ground.py`](c1/ground.py#L36) 36행**

```python
"아래 자료를 참고해 질문에 세 문장 이내로 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`c1/ground.py`](c1/ground.py#L37) 37행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`c1/ground.py`](c1/ground.py#L39) 39행**

```python
"자료:\n{ctx}\n\n문장: {s}\n\n이 문장의 내용이 자료에 나와 있으면 '있음', 자료에 없는 내용이 들어 있으면 '없음'이라고만 답하세요. 자료에 없다고 밝히는 문장은 '있음'입니다."
```

## [41. 에이전트 검색 · 벡터 대신 grep](lessons/41-C2-1/README.md)

**[`c2/agent.py`](c2/agent.py#L45) 45행**

```python
"도구로 문서를 찾아 읽고, 문서에 근거해 세 문장 이내로 답하세요."
```

**[`c2/agent.py`](c2/agent.py#L60) 60행**

```python
"질문: {q}\n정답 근거: {src}\n답: {a}\n\n답이 정답 근거와 맞으면 '맞음', 틀리거나 모른다고 했으면 '틀림'이라고만 답하세요."
```

**[`c2/agent.py`](c2/agent.py#L78) 78행**

```python
"아래 자료를 참고해 질문에 세 문장 이내로 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [42. 질문을 SQL로 · 텍스트→SQL](lessons/42-C2-2/README.md)

**[`c2/sql.py`](c2/sql.py#L43) 43행**

```python
"\n규칙: 사람 이름과 장르는 표기가 여러 가지라 = 대신 LIKE '%핵심어%'로 찾으세요. author가 빈 칸('')인 책은 작가 미상입니다."
```

**[`c2/sql.py`](c2/sql.py#L47) 47행**

```python
f"SQLite 표:\n{SCHEMA}{extra}\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}"
```

## [43. 한 표로 비교 · 질문마다 길 고르기](lessons/43-C2-3/README.md)

**[`c2/route.py`](c2/route.py#L17) 17행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [44. API로 띄우고 · 지연과 비용 재기](lessons/44-D1/README.md)

**[`d1/api.py`](d1/api.py#L21) 21행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [45. 권한 필터와 누출 테스트](lessons/45-D2/README.md)

**[`d2/permit.py`](d2/permit.py#L35) 35행**

```python
"아래 자료에 나온 내용만으로 답하세요. 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [47. 문서 속의 공격 · 간접 프롬프트 인젝션](lessons/47-D4/README.md)

**[`d4/inject.py`](d4/inject.py#L38) 38행**

```python
"아래 자료를 참고해 질문에 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [48. 로그와 트레이스 · 일어난 일을 나중에 찾기](lessons/48-D5/README.md)

**[`d5/trace.py`](d5/trace.py#L37) 37행**

```python
"아래 자료에 나온 내용만으로 답하세요. 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [49. 서비스로 나누기 — API · 저장소 · 캐시](lessons/49-D6/README.md)

**[`d6/api.py`](d6/api.py#L19) 19행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

## [54. 사례 · Apple Music 다국어 검색 — 어휘 색인에 임베딩 더하기](lessons/54-E2/README.md)

**[`e2/make_queries.py`](e2/make_queries.py#L31) 31행**

```python
"다음 책을 찾는 사람이 검색창에 칠 법한 짧은 묘사형 검색어를 하나만 쓰세요. 제목과 작가 이름의 낱말은 쓰지 마세요. 검색어만 출력하세요.\n\n제목: {t}\n작가: {a}\n소개: {d}"
```

## [56. 사례 · Uber QueryGPT — 표가 많을 때 텍스트→SQL](lessons/56-E4/README.md)

**[`e4/querygpt.py`](e4/querygpt.py#L39) 39행**

```python
"SQLite 표:\n" + "\n\n".join(SCHEMA[t] for t in tables) + f"\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}"
```

**[`e4/querygpt.py`](e4/querygpt.py#L45) 45행**

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

## [57. 현업 사례 · 사내 지식 챗봇 — '전부 알려줘'에는 다른 길](lessons/57-E5/README.md)

**[`e5/agg.py`](e5/agg.py#L45) 45행**

```python
f"자료:\n{ctx}\n\n자료에 근거해서 답하세요. 제목은 [ ] 안의 표기 그대로.\n질문: {q}"
```

**[`e5/agg.py`](e5/agg.py#L53) 53행**

```python
f"아래 질문의 대상이 문서 본문에 그대로 적혀 있을 짧은 낱말 하나만 출력하세요. 예: 상 이름, 사람 이름.\n질문: {q}"
```

**[`e5/agg.py`](e5/agg.py#L59) 59행**

```python
f"자료:\n{ctx}\n\n질문에 해당하는 책의 제목만 [ ] 표기 그대로 한 줄에 하나씩 출력하세요. 없으면 '없음'.\n질문: {q}"
```

**풀이에서 추가**

```python
return "집계" if "집계" in ask(f"질문이 자료 한두 개로 답하는 '조회'인지, 해당하는 것을 전부 모아야 하는 '집계'인지 한 단어로 답하세요.\n질문: {q}") else "조회"
```

## [59. 최종 미션 — 지원서에 넣을 RAG 평가 리포트](lessons/59-M1/README.md)

**[`mission/report.py`](mission/report.py#L22) 22행**

```python
"아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
```

**[`mission/report.py`](mission/report.py#L23) 23행**

```python
"자료:\n{ctx}\n\n답:\n{a}\n\n답의 모든 내용이 자료로 뒷받침되면 '예', 자료에 없는 내용이 하나라도 있으면 '아니오'라고만 답하세요."
```
