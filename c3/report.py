"""성적표: c3/results.jsonl(실행)과 c3/judged.jsonl(심판)을 묶어 표로. 실행: python c3/report.py
- 맞음: 심판 판정. 글자: 정답 글자 일치(보조). 근거: 필요한 근거 문서를 모두 read로 연 실행 수. 발췌: 발췌로라도 모두 본 실행 수.
- 한도: 턴 한도나 토큰 한도에 걸려 답을 못 낸 실행(오답과 따로 센다)."""
import json
import os
import statistics
from collections import defaultdict

qs = {q["id"]: q for q in json.load(open("c3/questions.json"))}
judged = {j["run"]: j for j in map(json.loads, open("c3/judged.jsonl"))} if os.path.exists("c3/judged.jsonl") else {}
rows = [json.loads(x) for x in open("c3/results.jsonl")]
NAME = {"search": "검색만", "raw": "통째로", "pull": "끌어와서"}
LEVEL = {"easy": "쉬운", "hard": "어려운", "none": "자료에 없음"}


def full(frac):
    a, b = frac.split("/")
    return a == b and b != "0"


groups = defaultdict(list)
for r in rows:
    groups[(r["set"], r["rep"], qs[r["q"]]["level"], r["mode"])].append(r)

print("### 한눈에 (심판 판정으로 맞은 수 · 쉬운 10 / 어려운 8 / 자료에 없음 3)")
print("| 집합 · 반복 | 방식 | 맞음 / 21 | 쉬운 | 어려운 | 없음 | 한도 | 질문당 시간 | 질문당 입력 토큰 | 비용 |\n|---|---|---|---|---|---|---|---|---|---|")
for (set_name, rep) in sorted({(k[0], k[1]) for k in groups}, key=lambda k: (["10k", "100k", "all"].index(k[0]), k[1])):
    for mode in NAME:
        by = {lv: groups.get((set_name, rep, lv, mode), []) for lv in LEVEL}
        g = sum(by.values(), [])
        ok = {lv: sum(judged.get(r["run"], {}).get("verdict") == "맞음" for r in v) for lv, v in by.items()}
        print(f"| {set_name} #{rep} | {NAME[mode]} | {sum(ok.values())} | {ok['easy']} | {ok['hard']} | {ok['none']} | {sum(r['status'] != 'answered' for r in g)} | "
              f"{statistics.mean(r['sec'] for r in g):.1f}초 | {statistics.mean(r['tokens_in'] for r in g):,.0f} | ${sum(r['cost'] for r in g):.2f} |")

for (set_name, rep) in sorted({(k[0], k[1]) for k in groups}, key=lambda k: (["10k", "100k", "all"].index(k[0]), k[1])):
    print(f"\n### {set_name} · {rep}번째 실행")
    print("| 문항 | 방식 | 실행 | 맞음 | 글자 | 한도 | 근거 다 엶 | 발췌로 다 봄 | 도구 | 시간 초과 | 잘림 | 입력 토큰 | 시간 | 비용 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for level in LEVEL:
        for mode in NAME:
            g = groups.get((set_name, rep, level, mode))
            if not g:
                continue
            ok = sum(judged.get(r["run"], {}).get("verdict") == "맞음" for r in g)
            cap = sum(r["status"] != "answered" for r in g)
            st = lambda s: sum(r["by_status"].get(s, 0) for r in g)  # noqa: E731
            ev = "-" if level == "none" or mode == "search" else str(sum(full(r["evidence"]) for r in g))  # 검색만에는 read가 없다
            gl = "-" if level == "none" else str(sum(full(r["glimpsed"]) for r in g))
            print(f"| {LEVEL[level]} {len(g)} | {NAME[mode]} | {len(g)} | {ok} | {sum(r['correct'] for r in g)} | {cap} | {ev} | {gl} | {statistics.mean(r['tools'] for r in g):.1f} | {st('timeout')} | {st('truncated')} | "
                  f"{statistics.mean(r['tokens_in'] for r in g):,.0f} | {statistics.mean(r['sec'] for r in g):.1f}초 | ${sum(r['cost'] for r in g):.3f} |")

print("\n### 심판과 글자 일치가 엇갈린 실행 (사람이 다시 볼 것)")
for r in rows:
    j = judged.get(r["run"])
    if j and r["status"] == "answered" and (j["verdict"] == "맞음") != r["correct"]:
        print(f"- {r['set']} #{r['rep']} {r['q']} {NAME[r['mode']]} · 심판 {j['verdict']} · 글자 {'○' if r['correct'] else '✕'} · 정답 {qs[r['q']]['answers'] or '자료에 없음'} · 답 「{j['last'][:80]}」")

reps = defaultdict(lambda: defaultdict(list))  # 세 번 반복한 집합: 문항별로 몇 번 맞았나
for r in rows:
    if r["set"] == "all":
        reps[r["mode"]][r["q"]].append(judged.get(r["run"], {}).get("verdict") == "맞음")
if any(len(v) > 1 for m in reps.values() for v in m.values()):
    print("\n### 전체 집합 · 실행마다의 흔들림 (문항별 맞은 횟수/실행 횟수)")
    print("| 문항 | " + " | ".join(NAME.values()) + " |\n|---|---|---|---|")
    for qid in qs:
        print(f"| {qid} {qs[qid]['kind']} | " + " | ".join(f"{sum(reps[m][qid])}/{len(reps[m][qid])}" for m in NAME) + " |")
    for m in NAME:
        totals = [sum(v[i] for v in reps[m].values() if len(v) > i) for i in range(max(len(v) for v in reps[m].values()))]
        print(f"- {NAME[m]}: 실행별 맞은 수 {totals} · 중앙값 {statistics.median(totals)}")
print(f"\n누적 비용 ${sum(r['cost'] for r in rows):.2f} · 실행 {len(rows)}회")

# ── 보조 실험(c3/extra.jsonl): 끌어오는 개수 고정 · 한 번에 답하기 · 라우터 ──
if os.path.exists("c3/extra.jsonl"):
    X = [json.loads(x) for x in open("c3/extra.jsonl")]
    ok = lambda r: judged.get(r["run"], {}).get("verdict") == "맞음"  # noqa: E731
    mean = lambda g, k: statistics.mean(r[k] for r in g)  # noqa: E731
    print("\n### 끌어오는 개수 고정 (65만 · 어려운 8문항)\n| 한 번에 | 반복 | 맞음 | 한도 | 근거 다 엶 | 도구 | 작업 폴더 | 입력 토큰 | 시간 | 비용 |\n|---|---|---|---|---|---|---|---|---|---|")
    for k in (20, 100, 300):
        for rep in (1, 2, 3):
            g = [r for r in X if r["exp"] == f"k{k}" and r["rep"] == rep]
            if g:
                print(f"| {k}개 | {rep} | {sum(map(ok, g))} | {sum(r['status'] != 'answered' for r in g)} | {sum(full(r['evidence']) for r in g)} | {mean(g, 'tools'):.1f} | {mean(g, 'work'):.0f} | {mean(g, 'tokens_in'):,.0f} | {mean(g, 'sec'):.1f}초 | ${sum(r['cost'] for r in g):.3f} |")
    print("\n### 넘기기 (65만 · 21문항). 1단계가 답을 못 내거나 모른다고 하면 끌어와서 뒤지기로 넘긴다\n| 1단계 | 반복 | 넘김 | 최종 맞음 | 1단계에서 끝낸 답 중 맞음 | 질문당 시간 | 질문당 입력 토큰 | 비용 |\n|---|---|---|---|---|---|---|---|")
    pull = {(r["rep"], r["q"]): r for r in rows if r["set"] == "all" and r["mode"] == "pull"}
    for name, exp in (("검색만 다섯 턴(실제 실행)", "router"), ("한 번 검색·한 번 답(2단계는 본 실측의 같은 회차를 이어 붙인 계산)", "oneshot")):
        for rep in (1, 2, 3):
            s1 = {r["q"]: r for r in X if r["exp"] == exp and r["rep"] == rep and r.get("stage", 1) == 1}
            go = [q for q, r in s1.items() if r["status"] != "answered" or r["refused"]]
            s2 = {r["q"]: r for r in X if r["exp"] == exp and r["rep"] == rep and r.get("stage") == 2} if exp == "router" else {q: pull[(rep, q)] for q in go if (rep, q) in pull}
            if not s1:
                continue
            both = list(s1.values()) + list(s2.values())
            print(f"| {name} | {rep} | {len(go)} | {sum(ok(s2.get(q, s1[q])) for q in s1)} | {sum(ok(s1[q]) for q in s1 if q not in go)}/{len(s1) - len(go)} | {sum(r['sec'] for r in both) / len(s1):.1f}초 | {sum(r['tokens_in'] for r in both) / len(s1):,.0f} | ${sum(r['cost'] for r in both):.3f} |")
    one = [r for r in X if r["exp"] == "oneshot"]
    if one:
        by = lambda lv: "·".join(str(sum(ok(r) for r in one if r["rep"] == rep and qs[r["q"]]["level"] == lv)) for rep in (1, 2, 3))  # noqa: E731
        print(f"\n한 번 검색·한 번 답만(넘기지 않음): 쉬운 {by('easy')} / 어려운 {by('hard')} / 없음 {by('none')} · 질문당 {mean(one, 'sec'):.1f}초 · 입력 {mean(one, 'tokens_in'):,.0f} · 한 바퀴 ${sum(r['cost'] for r in one) / 3:.3f} · 틀린 답 {sum(judged.get(r['run'], {}).get('verdict') == '틀림' for r in one)}회")
    print(f"\n보조 실험 비용 ${sum(r['cost'] for r in X):.2f} · 실행 {len(X)}회")
