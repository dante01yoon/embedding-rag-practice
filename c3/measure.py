"""전체 실측: 집합 → 반복 → 문항 → 방식 순서로 한 번에 하나씩 돌린다(시간이 서로 섞이지 않게).
실행: python c3/measure.py
- 중간에 멈춰도 다시 실행하면 끝난 것은 건너뛰고 이어서 한다(c3/results.jsonl).
- c3/runs/ 전체의 누적 비용이 LIMIT 달러를 넘으면 멈춘다.
- 실행 조건은 c3/config.json에 남긴다. 조건을 바꾸면 결과 파일을 새로 시작해야 한다."""

import glob
import json
import os
import sys
import time

sys.path.insert(0, "c3")
import agent  # noqa: E402
import tools  # noqa: E402

PLAN = [("all", 1), ("100k", 1), ("10k", 1), ("all", 2), ("all", 3)]  # (집합, 몇 번째 반복)
MODES = ["search", "raw", "pull"]
LIMIT = 7.5
OUT = "c3/results.jsonl"

config = {
    "model": agent.MODEL,
    "max_turns": agent.MAX_TURNS,
    "token_cap": agent.TOKEN_CAP,
    "temperature": 0,
    "system": agent.SYSTEM,
    "tools": {
        "page": tools.PAGE,
        "read_chars": tools.READ_CHARS,
        "find_timeout": tools.FIND_TIMEOUT,
        "pull": [tools.PULL_MIN, tools.PULL_MAX],
        "work_max": tools.WORK_MAX,
        "snippet": tools.SNIPPET,
    },
    "index": "Kiwi 형태소(N·V·S) · SQLite FTS5 · 제목 5 : 본문 1 · 본문 전체",
    "plan": PLAN,
    "started": time.strftime("%Y-%m-%d %H:%M"),
}
if not os.path.exists("c3/config.json"):
    json.dump(config, open("c3/config.json", "w"), ensure_ascii=False, indent=1)

qs = json.load(open("c3/questions.json"))
done = set()
if os.path.exists(OUT):
    done = {(r["set"], r["rep"], r["q"], r["mode"]) for r in map(json.loads, open(OUT))}


def row(r, rep):  # 실행 기록에서 표에 쓸 칸만 고른다
    keep = ("run", "q", "mode", "set", "status", "correct", "refused", "evidence", "glimpsed")
    keep += ("turns", "tokens_in", "tokens_out", "cost", "sec", "work")
    seen = {c["status"] for c in r["tools"]}
    by_status = {s: sum(c["status"] == s for c in r["tools"]) for s in seen}
    return {k: r[k] for k in keep} | {"rep": rep, "tools": len(r["tools"]), "by_status": by_status}


def spent():
    return sum(json.load(open(f)).get("cost") or 0 for f in glob.glob("c3/runs/*.json"))


errors = 0
for set_name, rep in PLAN:
    for q in qs:
        for mode in MODES:
            if (set_name, rep, q["id"], mode) in done:
                continue
            if spent() > LIMIT:
                sys.exit(f"누적 비용 한도 {LIMIT}달러에서 멈춤")
            try:
                r = agent.solve(q, mode, set_name)
                errors = 0
            except Exception as e:  # 한 실행이 죽어도 전체는 계속. 연달아 다섯 번이면 멈춘다
                errors += 1
                print(f"{set_name} #{rep} {q['id']} {mode} 실패: {str(e)[:150]}", flush=True)
                if errors >= 5:
                    sys.exit("연달아 실패해서 멈춤")
                continue
            with open(OUT, "a") as f:
                f.write(json.dumps(row(r, rep), ensure_ascii=False) + "\n")
            print(
                f"{set_name:4} #{rep} {q['id']} {mode:6} {r['status']:9} "
                f"{'○' if r['correct'] else '✕'} 근거 {r['evidence']} · "
                f"턴 {r['turns']:2} · 도구 {len(r['tools']):2} · "
                f"입력 {r['tokens_in']:>7,} · ${r['cost']:.4f} · {r['sec']:5.1f}초",
                flush=True,
            )
print(f"끝 · 누적 비용 ${spent():.2f}")
