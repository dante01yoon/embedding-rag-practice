"""논문 읽기 수업 과제용 로그 둘을 만든다. 실행: python c3/make_logs.py
실행 기록(c3/runs/)에는 도구 호출의 인자만 남아 있어서, 같은 검색어를 같은 색인에 다시 넣어 돌려받은 글까지 적는다.
검색 도구는 같은 색인·같은 검색어에 늘 같은 결과를 주므로, 여기 적힌 발췌는 그때 모델이 받은 것과 같다."""
import json
import os
import sys

sys.path.insert(0, "c3")
from tools import Box  # noqa: E402

PICK = [("A-래퍼-검색만", "all", 1, "h02"), ("B-초등학교-검색만", "100k", 1, "h08")]
qs = {q["id"]: q for q in json.load(open("c3/questions.json"))}
rows = [json.loads(x) for x in open("c3/results.jsonl")]
os.makedirs("c3/logs", exist_ok=True)
for name, set_name, rep, qid in PICK:
    r = next(r for r in rows if (r["set"], r["rep"], r["q"], r["mode"]) == (set_name, rep, qid, "search"))
    rec = json.load(open(f"c3/runs/{r['run']}.json"))
    box = Box(set_name, "search", "replay")
    out = [f"# 로그 {name[0]} · 검색만 · 문서 묶음 {set_name}", "", f"질문: {qs[qid]['question']}", f"끝난 상태: {rec['status']} · 검색 {len(rec['tools'])}번 · {rec['sec']}초", ""]
    for i, t in enumerate(rec["tools"], 1):
        out += [f"## 검색 {i}: {t['args']['query']}", "", box.search(t["args"]["query"]), ""]
    out += ["## 마지막 답", "", rec["answer"] or "(답 없음: 한도에 걸림)"]
    open(f"c3/logs/{name}.md", "w", encoding="utf-8").write("\n".join(out))
    print(name, len(rec["tools"]), "번", sum(len(x) for x in out), "자")
