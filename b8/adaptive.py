import json
import sys
from typing import TypedDict

from langgraph.graph import END, StateGraph

sys.path.insert(0, "b8")
import crag  # noqa: E402  지난 수업의 그래프 (검색 → 채점 → 다시 쓰기 → 답하기)

calls = 0
ask_once = crag.ask


def ask(prompt):  # LLM을 몇 번 부르는지 센다
    global calls
    calls += 1
    return ask_once(prompt)


crag.ask = ask


class State(TypedDict):
    question: str
    route: str
    answer: str


ROUTE = "다음 입력을 하나로 분류해 한 단어로만 답하세요. 인사나 잡담이면 chat, 쿠버네티스 문서에서 찾아야 하는 질문이면 search, 쿠버네티스와 관계없는 질문이면 none.\n\n{q}"


def route(s):  # 노드 1: 입력의 종류 고르기
    return {"route": ask(ROUTE.format(q=s["question"])).strip().lower()}


def chat(s):  # 잡담은 검색 없이 바로
    return {"answer": ask(f"다음 인사나 잡담에 한 문장으로 친절하게 답하고, 쿠버네티스 질문은 편하게 하라고 덧붙이세요.\n\n{s['question']}")}


def search(s):  # 문서 질문은 지난 수업의 그래프로
    out = crag.app.invoke({"question": s["question"], "query": s["question"], "found": [], "tries": 0, "answer": ""})
    return {"answer": out["answer"]}


def none(s):  # 관계없는 질문은 LLM 없이 정해진 문장
    return {"answer": "쿠버네티스 문서에 대한 질문에만 답할 수 있어요."}


g = StateGraph(State)
for name, fn in [("route", route), ("chat", chat), ("search", search), ("none", none)]:
    g.add_node(name, fn)
g.set_entry_point("route")
g.add_conditional_edges("route", lambda s: s["route"], {"chat": "chat", "search": "search", "none": "none"})
for name in ["chat", "search", "none"]:
    g.add_edge(name, END)
app = g.compile()

EVERYDAY = ["안녕하세요!", "고마워요, 덕분에 해결했어요", "오늘 날씨 어때요?", "파이썬 리스트 정렬하는 법 알려줘", "ㅋㅋ 오늘도 에러 파티네요",
            "리눅스에서 디스크 용량 확인하는 명령어", "점심 메뉴 추천해 줘", "좋은 하루 보내세요"]
for q in EVERYDAY[:3]:
    out = app.invoke({"question": q, "route": "", "answer": ""})
    print(f"{out['route']:6s} ← {q}\n  {out['answer'][:80]}")

inputs = EVERYDAY + [x["question"] for x in json.load(open("k8s/qa_ko_short.json"))]  # 잡담 8 + 문서 질문 39
calls = 0
for q in inputs:
    crag.app.invoke({"question": q, "query": q, "found": [], "tries": 0, "answer": ""})
always = calls
calls = 0
for q in inputs:
    app.invoke({"question": q, "route": "", "answer": ""})
print(f"입력 {len(inputs)}개 | LLM 호출: 늘 그래프 {always}번 · 길 고르기 {calls}번")
json.dump(crag.cache, open(crag.CACHE, "w"), ensure_ascii=False, indent=1)
