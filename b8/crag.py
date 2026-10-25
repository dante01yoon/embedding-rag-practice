import json
import os
import sys
from typing import TypedDict

import numpy as np
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], d["title"], c) for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
model = SentenceTransformer("BAAI/bge-m3")
CACHE = "k8s/llm_cache_b8.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


class State(TypedDict):  # 그래프가 노드 사이로 들고 다니는 메모
    question: str
    query: str
    found: list
    tries: int
    answer: str


def retrieve(s):  # 노드 1: 지금 검색어로 청크 4개
    top = np.argsort(-(vecs @ model.encode(s["query"], normalize_embeddings=True)))[:4]
    return {"found": [int(i) for i in top], "tries": s["tries"] + 1}


def grade(s):  # 노드 2: 청크마다 질문과 관련 있는지 LLM이 채점, 관련 있는 것만 남긴다
    keep = [i for i in s["found"] if ask(f"질문: {s['question']}\n\n자료: {chunks[i][2]}\n\n이 자료가 질문에 답하는 데 도움이 되면 '예', 아니면 '아니오'라고만 답하세요.").startswith("예")]
    return {"found": keep}


def rewrite(s):  # 노드 3: 검색이 잘 되도록 질문을 다시 쓴다
    return {"query": ask(f"다음 질문을 쿠버네티스 공식 문서에서 찾기 좋은 검색 문장 하나로 다시 써 주세요. 검색 문장만 출력하세요.\n\n{s['question']}")}


def generate(s):  # 노드 4: 남은 청크로만 답한다
    ctx = "\n\n".join(f"[{n + 1}] {chunks[i][1]}\n{chunks[i][2]}" for n, i in enumerate(s["found"]))
    return {"answer": ask(f"아래 자료만 보고 답하세요. 자료에 답이 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {s['question']}")}


def decide(s):  # 갈림길: 관련 청크가 있으면 답하고, 없으면 질문을 고쳐 다시 찾는다
    if s["found"] or s["tries"] >= 2:  # 두 번 찾아도 없으면 그만
        return "generate"
    return "rewrite"


g = StateGraph(State)
for name, fn in [("retrieve", retrieve), ("grade", grade), ("rewrite", rewrite), ("generate", generate)]:
    g.add_node(name, fn)
g.set_entry_point("retrieve")
g.add_edge("retrieve", "grade")
g.add_conditional_edges("grade", decide, {"generate": "generate", "rewrite": "rewrite"})
g.add_edge("rewrite", "retrieve")
g.add_edge("generate", END)
app = g.compile()

if __name__ == "__main__":  # 다른 파일에서 불러올 때는 실행하지 않는다
    for q in ["emptyDir 저장소 위치", "AWS EKS 클러스터는 한 시간에 요금이 얼마예요?"]:
        out = app.invoke({"question": q, "query": q, "found": [], "tries": 0, "answer": ""})
        print(f"{q} → 검색 {out['tries']}번 · 관련 청크 {len(out['found'])}개\n  {out['answer'][:120]}")
    short = json.load(open("k8s/qa_ko_short.json"))  # 검색창처럼 짧게 줄인 질문 39개
    plain = graph = again = 0
    for item in short:
        q = item["question"]
        top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:4]
        plain += any(chunks[i][0] == item["path"] for i in top)  # 그냥 검색: 상위 4개에 정답 문서
        out = app.invoke({"question": q, "query": q, "found": [], "tries": 0, "answer": ""})
        graph += any(chunks[i][0] == item["path"] for i in out["found"])  # 그래프: 남긴 청크에 정답 문서
        again += out["tries"] > 1
    print(f"짧은 질문 {len(short)}개 | 그냥 검색 {plain} · 그래프 {graph} · 다시 찾음 {again}")
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
