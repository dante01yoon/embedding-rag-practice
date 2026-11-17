"""길 고르기: 먼저 한 번 검색해 한 번에 답하고, 모른다고 하면 끌어와서 뒤지기로 넘긴다.
실행: python c3/router.py <질문 id> [10k|100k|all]"""

import json
import sys
import time

sys.path.insert(0, "c3")
import agent  # noqa: E402
from tools import Box  # noqa: E402

ONE = (
    "한국어 위키백과에서 검색기가 고른 발췌만 보고 질문에 답하세요. "
    "마지막에 한 줄로 '답: …'을 쓰고, 발췌에 근거가 없으면 '답: 모름'이라고 쓰세요."
)


def oneshot(q, set_name):  # 1단계: 질문 문장으로 한 번 검색하고, 발췌 다섯 개만 보고 한 번에 답한다
    found = Box(set_name, "search", "oneshot").search(q["question"])
    msgs = [
        {"role": "system", "content": ONE},
        {"role": "user", "content": f"{q['question']}\n\n검색 결과:\n{found}"},
    ]
    r = agent.ask(msgs, None)
    return r.choices[0].message.content or "", (r.usage.model_extra or {}).get("cost") or 0


def route(q, set_name="all"):
    t0 = time.time()
    answer, cost = oneshot(q, set_name)
    path = ["한 번에 답하기"]
    if "모름" in answer.rsplit("답:", 1)[-1]:  # 모른다고 하면 2단계로 넘긴다
        r = agent.solve(q, "pull", set_name)
        answer, cost = r["answer"], cost + r["cost"]
        # answered · turn_cap · token_cap을 그대로 남긴다
        path.append(f"끌어와서 뒤지기({r['status']})")
    return {"answer": answer, "path": path, "cost": cost, "sec": round(time.time() - t0, 1)}


if __name__ == "__main__":
    q = next(x for x in json.load(open("c3/questions.json")) if x["id"] == sys.argv[1])
    r = route(q, sys.argv[2] if len(sys.argv) > 2 else "all")
    print(" → ".join(r["path"]), f"· ${r['cost']:.4f} · {r['sec']}초")
    print(r["answer"][-200:])
