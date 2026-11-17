"""질문 하나를 세 방식 가운데 하나로 푸는 에이전트.
실행: python c3/agent.py <질문 id> <search|raw|pull> <10k|100k|all>
- search: 검색기가 고른 구간만 본다.
- raw: 문서 묶음 전체를 직접 뒤진다.  pull: 검색기로 작업 폴더에 끌어온 문서만 뒤진다.
- 세 방식 모두 다시 물을 수 있고, 턴 한도·출력 크기·도구 제한 시간이 같다.
- 측정용이라 응답 캐시를 쓰지 않는다. 실행마다 모델·토큰·비용·시간·도구 상태를 c3/runs/에 남긴다."""

import json
import os
import re
import sys
import time
import uuid

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, "c3")
from tools import Box  # noqa: E402

load_dotenv()
llm = OpenAI()
MODEL = os.environ["MODEL"]
MAX_TURNS = 20  # 모델에게 묻는 횟수 한도
TOKEN_CAP = 300_000  # 질문 하나에 쓰는 입력 토큰 한도

SYSTEM = (
    "한국어 위키백과 문서 묶음에서 근거를 찾아 질문에 답하세요. "
    "도구로 직접 확인한 내용만 근거로 삼으세요. "
    "마지막에 한 줄로 '답: …'을 쓰고, 끝내 찾지 못하면 '답: 모름'이라고 쓰세요."
)
S, N = {"type": "string"}, {"type": "integer"}


def tool(name, desc, props, need):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": props, "required": need},
        },
    }


SEARCH = tool(
    "search",
    "검색기(BM25)로 문서를 찾는다. "
    "상위 5개 문서마다 검색어가 가장 많이 겹치는 700자 구간을 보여 준다"
    "(문서 앞부분이 아닐 수 있다). 문서 전체는 볼 수 없다.",
    {"query": S},
    ["query"],
)
READ = tool(
    "read",
    "문서 번호(w000123 꼴)로 문서를 1,200자씩 읽는다. "
    "at에 정규식을 주면 그 패턴이 처음 나오는 곳 근처부터 보여 주고, offset으로 이어 읽는다.",
    {"doc_id": S, "at": S, "offset": N},
    ["doc_id"],
)
FIND = (
    "정규식(대소문자 무시)이 든 문서를 {where} 찾는다. "
    "결과에는 이름(r1, r2 …)이 붙고, 문서 번호·제목·일치한 곳 주변 글자가 20개씩 나온다. "
    "within에 앞선 결과 이름을 주면 그 문서들 안에서만 다시 찾는다"
    "(조건 둘을 모두 만족하는 문서 찾기). offset으로 다음 20개를 본다. 한 번에 20초까지."
)
FIND_P = {"pattern": S, "within": S, "offset": N}
PULL = tool(
    "pull",
    "검색기(BM25) 상위 k개 문서를 작업 폴더로 가져온다"
    "(k는 50~300, 기본 100, 작업 폴더 전체 1,500개까지). "
    "가져오는 데는 토큰이 거의 들지 않으니 넉넉히 가져온다. 이미 있는 문서는 건너뛴다. "
    "순위 상위 20개의 문서 번호와 제목을 미리 보여 준다.",
    {"query": S, "k": N},
    ["query"],
)
TOOLS = {
    "search": [SEARCH],
    "raw": [tool("find", FIND.format(where="문서 묶음 전체에서"), FIND_P, ["pattern"]), READ],
    "pull": [
        PULL,
        tool("find", FIND.format(where="작업 폴더 안에서만"), FIND_P, ["pattern"]),
        READ,
    ],
}
NOTE = {
    "search": "",
    "raw": "",
    "pull": (
        " 처음에는 작업 폴더가 비어 있습니다. "
        "find와 read는 작업 폴더에 가져온 문서에만 쓸 수 있습니다."
    ),
}


def ask(msgs, tools):  # 잠깐의 통신 오류는 세 번까지 다시
    for wait in (2, 10, 30, None):
        try:
            return llm.chat.completions.create(
                model=MODEL,
                messages=msgs,
                temperature=0,
                extra_body={"usage": {"include": True}},
                **({"tools": tools} if tools else {}),
            )
        except Exception:
            if wait is None:
                raise
            time.sleep(wait)


def solve(q, mode, set_name):
    run = f"{q['id']}-{mode}-{set_name}-{uuid.uuid4().hex[:6]}"
    box = Box(set_name, mode, run)
    msgs = [
        {"role": "system", "content": SYSTEM + NOTE[mode]},
        {"role": "user", "content": q["question"]},
    ]
    turns, answer, status, served, t0 = [], "", "turn_cap", None, time.time()
    try:
        for _ in range(MAX_TURNS):
            r = ask(msgs, TOOLS[mode])
            u, m = r.usage, r.choices[0].message
            served = (r.model, getattr(r, "provider", None))
            cost = (u.model_extra or {}).get("cost")
            turns.append({"in": u.prompt_tokens, "out": u.completion_tokens, "cost": cost})
            if not m.tool_calls:  # 도구를 부르지 않으면 그게 최종 답
                answer, status = m.content or "", "answered"
                break
            calls = []
            for t in m.tool_calls:
                fn = {"name": t.function.name, "arguments": t.function.arguments}
                calls.append({"id": t.id, "type": "function", "function": fn})
            msgs.append({"role": "assistant", "content": m.content or "", "tool_calls": calls})
            for t in m.tool_calls:
                try:
                    args = json.loads(t.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {"_": t.function.arguments}  # 읽지 못한 인자는 그대로 넘겨 bad_request로
                out = box.call(t.function.name, args)
                msgs.append({"role": "tool", "tool_call_id": t.id, "content": out})
            if sum(x["in"] for x in turns) > TOKEN_CAP:
                status = "token_cap"
                break
    finally:
        rec = {
            "run": run,
            "q": q["id"],
            "mode": mode,
            "set": set_name,
            "model": served,
            "status": status,
            "answer": answer,
            "turns": len(turns),
            "tokens_in": sum(x["in"] for x in turns),
            "tokens_out": sum(x["out"] for x in turns),
            "cost": sum(x["cost"] or 0 for x in turns),
            "sec": round(time.time() - t0, 1),
            "tools": box.log,
            "opened": [f"w{n:06d}" for n in sorted(box.opened)],
            "shown": [f"w{n:06d}" for n in sorted(box.shown)],
            "work": len(box.work),
            "per_turn": turns,
        }
        box.close()
    rec.update(grade(q, rec))
    os.makedirs("c3/runs", exist_ok=True)
    json.dump(rec, open(f"c3/runs/{run}.json", "w"), ensure_ascii=False, indent=1)
    return rec


def grade(q, rec):  # 예비 채점: 답 글자 일치 + 근거 문서를 실제로 봤는가
    said = re.sub(r"\s", "", rec["answer"].rsplit("답:", 1)[-1])
    need = set(q["docs"])  # 근거 문서 가운데 read로 연 것 / 발췌라도 본 것
    refused = "모름" in said
    # 자료에 없는 문항은 모른다고 해야 맞음
    hit = any(re.sub(r"\s", "", a) in said for a in q["answers"]) if q["answers"] else refused
    return {
        "correct": hit,
        "refused": refused,
        "evidence": f"{len(need & set(rec['opened']))}/{len(need)}",
        "glimpsed": f"{len(need & (set(rec['opened']) | set(rec['shown'])))}/{len(need)}",
    }


if __name__ == "__main__":
    qid, mode, set_name = sys.argv[1:4]
    q = next(x for x in json.load(open("c3/questions.json")) if x["id"] == qid)
    r = solve(q, mode, set_name)
    for c in r["tools"]:
        args = json.dumps(c["args"], ensure_ascii=False)[:110]
        print(f"  {c['tool']:6} {c['status']:12} {c['sec']:5.1f}초 {args}")
    print(
        f"{r['status']} · 맞음 {r['correct']} · 근거 {r['evidence']} · "
        f"턴 {r['turns']} · 도구 {len(r['tools'])} · "
        f"입력 {r['tokens_in']:,} · 출력 {r['tokens_out']:,} · ${r['cost']:.4f} · {r['sec']}초"
    )
    print(r["answer"][-300:])
