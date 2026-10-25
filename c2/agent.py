import json
import os
import subprocess
import sys

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_c2.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def chat(msgs, tools=None):  # 대화와 도구 설명을 열쇠로 캐시 · 도구 호출과 입력 토큰도 저장
    key = json.dumps([msgs, tools], ensure_ascii=False)
    if key not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=msgs, temperature=0, **({"tools": tools} if tools else {}))
        m = r.choices[0].message
        cache[key] = {"content": m.content, "tool_calls": [{"id": t.id, "name": t.function.name, "args": t.function.arguments} for t in (m.tool_calls or [])], "tokens": r.usage.prompt_tokens}
    return cache[key]


def grep(pattern):  # 문서 폴더에서 정규식으로 줄 찾기
    out = subprocess.run(["grep", "-rn", "-i", "-E", pattern, "k8s/ko"], capture_output=True, text=True).stdout.splitlines()
    return "\n".join(line[:200] for line in out[:30]) or "결과 없음"


def read(path, line):  # line번째 줄부터 40줄
    L = open(path).read().splitlines()
    line = max(1, int(line))
    return "\n".join(f"{i}: {L[i - 1]}" for i in range(line, min(len(L), line + 40) + 1))


TOOLS = [{"type": "function", "function": {"name": "grep", "description": "쿠버네티스 한국어 문서(k8s/ko)에서 정규식으로 줄을 찾는다. 결과: 경로:줄번호:내용 (최대 30줄)", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}}},
         {"type": "function", "function": {"name": "read", "description": "파일의 line번째 줄부터 40줄을 읽는다", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "line": {"type": "integer"}}, "required": ["path", "line"]}}}]


def agent(q, max_turns=8):  # 도구를 부르고 → 결과를 붙이고 → 다시 묻기를 답이 나올 때까지
    msgs = [{"role": "system", "content": "도구로 문서를 찾아 읽고, 문서에 근거해 세 문장 이내로 답하세요."}, {"role": "user", "content": q}]
    calls, tokens = 0, 0
    for _ in range(max_turns):
        m = chat(msgs, TOOLS)
        tokens += m["tokens"]
        if not m["tool_calls"]:
            return m["content"], calls, tokens
        msgs.append({"role": "assistant", "content": m["content"], "tool_calls": [{"id": t["id"], "type": "function", "function": {"name": t["name"], "arguments": t["args"]}} for t in m["tool_calls"]]})
        for t in m["tool_calls"]:
            calls += 1
            a = json.loads(t["args"])  # 모델이 고른 인자
            msgs.append({"role": "tool", "tool_call_id": t["id"], "content": grep(**a) if t["name"] == "grep" else read(**a)})
    return "(한도 초과)", calls, tokens


JUDGE = "질문: {q}\n정답 근거: {src}\n답: {a}\n\n답이 정답 근거와 맞으면 '맞음', 틀리거나 모른다고 했으면 '틀림'이라고만 답하세요."
QA = [x for x in json.load(open("k8s/qa_ko_short.json")) if "source" in x]


def right(x, a):
    return "맞음" in chat([{"role": "user", "content": JUDGE.format(q=x["question"], src=x["source"], a=a)}])["content"]


if __name__ == "__main__":  # 다른 파일에서 가져다 쓸 때는 실행하지 않음
    runs = [agent(x["question"]) for x in QA]
    ag = [right(x, a) for x, (a, _, _) in zip(QA, runs)]
    print(f"에이전트 grep | 맞힘 {sum(ag)}/{len(QA)} · 도구 평균 {np.mean([r[1] for r in runs]):.1f}번 · 입력 평균 {np.mean([r[2] for r in runs]):,.0f}토큰")

    docs = json.load(open("k8s/docs_ko.json"))  # 비교: 벡터 검색 청크 4개 (환각 수업의 '그냥' 답)
    chunks = [c for d in docs for c in split(d["text"], 500, 100)]
    vecs = np.load("k8s/vecs_ko_500.npy")
    model = SentenceTransformer("BAAI/bge-m3")
    c1 = json.load(open("k8s/llm_cache_c1.json"))
    P = "아래 자료를 참고해 질문에 세 문장 이내로 답하세요.\n\n{ctx}\n\n질문: {q}"
    rg, toks = [], []
    for x in QA:
        top = np.argsort(-(vecs @ model.encode(x["question"], normalize_embeddings=True)))[:4]
        p = P.format(ctx="\n\n".join(chunks[i] for i in top), q=x["question"])
        rg.append(right(x, c1[p]))
        toks.append(chat([{"role": "user", "content": p}])["tokens"])
    print(f"벡터 검색    | 맞힘 {sum(rg)}/{len(QA)} · 도구 0번 · 입력 평균 {np.mean(toks):,.0f}토큰")
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
