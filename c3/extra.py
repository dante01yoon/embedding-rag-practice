"""보조 실험 둘(65만 문서, 세 번씩). 실행: python c3/extra.py   (멈춰도 다시 실행하면 이어서 한다. 결과 c3/extra.jsonl)
1. 끌어오는 개수: pull이 한 번에 가져오는 문서 수를 20 · 100 · 300으로 고정하고 어려운 문항만.
2. 라우터: 먼저 검색만으로 다섯 턴. 답을 못 냈거나 모른다고 하면 끌어와서 뒤지기로 넘긴다(넘길 때 앞 단계의 대화는 버린다).
   다섯 턴은 본 실측을 보고 정한 값이다(검색만으로 맞힌 48회 중 39회가 다섯 턴 안). 같은 문항으로 정했으니 튜닝 결과로 읽는다."""
import glob
import json
import os
import sys

sys.path.insert(0, "c3")
import agent  # noqa: E402
import tools  # noqa: E402

LIMIT = 9.0  # c3/runs/ 전체 누적 비용(달러). 심판 몫을 남겨 둔다
OUT = "c3/extra.jsonl"
REPS = (1, 2, 3)
STAGE1_TURNS = 5
qs = json.load(open("c3/questions.json"))
done = {(r["exp"], r["rep"], r["q"], r.get("stage")) for r in map(json.loads, open(OUT))} if os.path.exists(OUT) else set()
PULL_FREE = agent.TOOLS["pull"][0]


def run(q, mode, **tag):
    if sum(json.load(open(f)).get("cost") or 0 for f in glob.glob("c3/runs/*.json")) > LIMIT:
        sys.exit(f"누적 비용 한도 {LIMIT}달러에서 멈춤")
    r = agent.solve(q, mode, "all")
    keep = ("run", "q", "mode", "set", "status", "correct", "refused", "evidence", "glimpsed", "turns", "tokens_in", "tokens_out", "cost", "sec", "work")
    row = {k: r[k] for k in keep} | tag | {"tools": len(r["tools"]), "by_status": {s: sum(c["status"] == s for c in r["tools"]) for s in {c["status"] for c in r["tools"]}}}
    with open(OUT, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{tag} {q['id']} {mode:6} {r['status']:9} {'○' if r['correct'] else '✕'} 근거 {r['evidence']} · 턴 {r['turns']:2} · 작업 {r['work']:4} · ${r['cost']:.4f} · {r['sec']:5.1f}초", flush=True)
    return r


for k in (20, 100, 300):  # 1. 끌어오는 개수 고정
    tools.PULL_MIN = tools.PULL_MAX = k  # pull이 k를 이 범위로 자르므로 항상 k개
    agent.TOOLS["pull"][0] = agent.tool("pull", f"검색기(BM25) 상위 {k}개 문서를 작업 폴더로 가져온다(한 번에 항상 {k}개, 작업 폴더 전체 1,500개까지). 이미 있는 문서는 건너뛴다. 순위 상위 20개의 문서 번호와 제목을 미리 보여 준다.", {"query": agent.S}, ["query"])
    for rep in REPS:
        for q in qs:
            if q["level"] == "hard" and (f"k{k}", rep, q["id"], None) not in done:
                run(q, "pull", exp=f"k{k}", rep=rep)
tools.PULL_MIN, tools.PULL_MAX, agent.TOOLS["pull"][0] = 50, 300, PULL_FREE

for rep in REPS:  # 2. 라우터: 검색만(다섯 턴) → 끌어와서 뒤지기
    for q in qs:
        if ("router", rep, q["id"], 2) in done:
            continue
        if ("router", rep, q["id"], 1) in done:
            first = next(r for r in map(json.loads, open(OUT)) if (r["exp"], r["rep"], r["q"], r.get("stage")) == ("router", rep, q["id"], 1))
        else:
            agent.MAX_TURNS = STAGE1_TURNS
            first = run(q, "search", exp="router", rep=rep, stage=1)
            agent.MAX_TURNS = 20
        if first["status"] != "answered" or first["refused"]:
            run(q, "pull", exp="router", rep=rep, stage=2)
print("끝")
