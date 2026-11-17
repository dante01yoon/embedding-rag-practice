"""참고 기준선: 한 번 검색해서 한 번에 답하기(다시 묻지 않는다). 65만 문서, 21문항, 세 번. 실행: python c3/oneshot.py
질문 문장을 그대로 검색어로 넣고, 상위 5개 문서의 700자 발췌만 보고 답한다. 도구가 없으니 모델 호출은 질문당 한 번이다.
결과는 c3/extra.jsonl에 exp="oneshot"으로 더한다(채점은 python c3/judge.py c3/extra.jsonl)."""

import json
import os
import sys
import time
import uuid

sys.path.insert(0, "c3")
import agent  # noqa: E402
from tools import Box  # noqa: E402

OUT = "c3/extra.jsonl"
SYSTEM = "한국어 위키백과에서 검색기가 고른 발췌만 보고 질문에 답하세요. 마지막에 한 줄로 '답: …'을 쓰고, 발췌에 근거가 없으면 '답: 모름'이라고 쓰세요."
done = (
    {(r["rep"], r["q"]) for r in map(json.loads, open(OUT)) if r["exp"] == "oneshot"}
    if os.path.exists(OUT)
    else set()
)
for rep in (1, 2, 3):
    for q in json.load(open("c3/questions.json")):
        if (rep, q["id"]) in done:
            continue
        run = f"{q['id']}-oneshot-all-{uuid.uuid4().hex[:6]}"
        box, t0 = Box("all", "search", run), time.time()
        found = box.call("search", {"query": q["question"]})
        r = agent.ask(
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"{q['question']}\n\n검색 결과:\n{found}"},
            ],
            None,
        )
        rec = {
            "run": run,
            "q": q["id"],
            "mode": "oneshot",
            "set": "all",
            "status": "answered",
            "answer": r.choices[0].message.content or "",
            "turns": 1,
            "tokens_in": r.usage.prompt_tokens,
            "tokens_out": r.usage.completion_tokens,
            "cost": (r.usage.model_extra or {}).get("cost") or 0,
            "sec": round(time.time() - t0, 1),
            "tools": box.log,
            "opened": [],
            "shown": [f"w{n:06d}" for n in sorted(box.shown)],
            "work": 0,
        }
        rec.update(agent.grade(q, rec))
        json.dump(rec, open(f"c3/runs/{run}.json", "w"), ensure_ascii=False, indent=1)
        keep = (
            "run",
            "q",
            "mode",
            "set",
            "status",
            "correct",
            "refused",
            "evidence",
            "glimpsed",
            "turns",
            "tokens_in",
            "tokens_out",
            "cost",
            "sec",
            "work",
        )
        with open(OUT, "a") as f:
            f.write(
                json.dumps(
                    {k: rec[k] for k in keep}
                    | {"exp": "oneshot", "rep": rep, "tools": 1, "by_status": {"ok": 1}},
                    ensure_ascii=False,
                )
                + "\n"
            )
        print(
            rep,
            q["id"],
            "○" if rec["correct"] else ("모름" if rec["refused"] else "✕"),
            f"발췌 {rec['glimpsed']} · 입력 {rec['tokens_in']:,} · ${rec['cost']:.4f} · {rec['sec']}초",
            flush=True,
        )
