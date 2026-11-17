"""강사의 실행 기록을 터미널에서 다시 본다(도구 호출 한 줄씩). 실행: python c3/show.py <이름>
이름: A(래퍼 질문 · 검색만) · raw(같은 질문 · 통째로 뒤지기) · pull(같은 질문 · 끌어와서 뒤지기) · miss(라이트 노벨 질문 · 끌어와서 뒤지기 첫 바퀴)
기록은 c3/results.jsonl과 c3/runs/에 있다. 모델을 다시 부르지 않으니 비용이 들지 않는다."""
import json
import sqlite3
import sys

PICK = {"A": ("all", 1, "h02", "search"), "raw": ("all", 1, "h02", "raw"), "pull": ("all", 1, "h02", "pull"), "miss": ("all", 1, "h06", "pull"), "h04": ("10k", 1, "h04", "raw")}
NAME = {"search": "검색만", "raw": "통째로 뒤지기", "pull": "끌어와서 뒤지기"}
END = {"answered": "답함", "turn_cap": "턴 한도", "token_cap": "토큰 한도"}
HEAD, TAIL = 6, 2  # 호출이 많으면 앞 여섯, 뒤 둘만 보여 준다

key = PICK[sys.argv[1]]
row = next(r for r in map(json.loads, open("c3/results.jsonl")) if (r["set"], r["rep"], r["q"], r["mode"]) == key)
rec = json.load(open(f"c3/runs/{row['run']}.json"))
q = next(x for x in json.load(open("c3/questions.json")) if x["id"] == key[2])
calls = rec["tools"]
SIZE = {"10k": "1만 개", "100k": "10만 개", "all": "약 65만 개"}
print(f"{NAME[key[3]]} · 문서 {SIZE[key[0]]} · 도구 호출 {len(calls)}번")
for i, c in enumerate(calls, 1):
    if len(calls) > HEAD + TAIL + 1 and HEAD < i <= len(calls) - TAIL:
        if i == HEAD + 1:
            print(f"    ⋮  {len(calls) - HEAD - TAIL}번 더")
        continue
    arg = c["args"].get("query") or c["args"].get("pattern") or c["args"].get("doc_id") or ""
    extra = "".join(f" {k}={v}" for k, v in c["args"].items() if k in ("k", "within", "at", "offset"))
    print(f"{i:3} {c['tool']:6} {c['status']:9} {c['sec']:5.1f}초  {arg[:44]}{extra[:24]}")
db = sqlite3.connect("wiki/docs.db")
seen = set(rec["opened"]) | set(rec["shown"])
marks = " · ".join(f"{db.execute('SELECT title FROM docs WHERE id=?', (int(d[1:]),)).fetchone()[0]} {'○' if d in seen else '✕'}" for d in q["docs"])
print(f"근거 문서: {marks}")
answer = rec["answer"].rsplit("답:", 1)[-1].strip().split("\n")[0][:30] if rec["answer"] else "없음"
print(f"끝: {END[rec['status']]}({rec['status']}) · 입력 {rec['tokens_in']:,}토큰 · {rec['sec']}초 · 답: {answer}")
