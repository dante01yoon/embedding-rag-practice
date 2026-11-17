"""실행 기록의 답을 LLM 심판이 채점한다.
실행: python c3/judge.py   (c3/results.jsonl에 있는 실행 가운데 아직 채점 안 한 것만)
- 심판은 어느 방식의 답인지 모른다. 질문, 정답, 근거 문장, 그리고 에이전트의 마지막 '답:' 줄만 본다.
- 한도에 걸려 답을 못 낸 실행은 심판에게 묻지 않고 '한도'로 적는다.
- 결과는 c3/judged.jsonl (실행 id, 판정, 이유).
  정답 글자 일치(correct)와 엇갈린 것은 사람이 다시 본다."""

import json
import os
import sys

sys.path.insert(0, "c3")
from agent import ask  # noqa: E402

PROMPT = """채점자입니다. 아래 '답'이 '정답'과 같은 것을 가리키는지 판정하세요.
- 표기가 달라도(한글·영어 이름, 띄어쓰기, 단위, 설명이 덧붙음) 같은 대상·같은 값이면 맞음.
- 답이 모른다·찾지 못했다는 뜻이면 모름.
- 정답이 '자료에 없음'이면, 모른다·자료에 없다고 답한 경우만 맞음이고 값을 지어냈으면 틀림.
JSON 한 줄로만 답하세요: {{"verdict": "맞음" | "틀림" | "모름", "reason": "한 문장"}}

질문: {q}
정답: {gold}
근거 문장: {ev}
답: {a}"""

qs = {q["id"]: q for q in json.load(open("c3/questions.json"))}
# 보조 실험은 python c3/judge.py c3/extra.jsonl
src = sys.argv[1] if len(sys.argv) > 1 else "c3/results.jsonl"
rows = [json.loads(x) for x in open(src)]
seen = set()
if os.path.exists("c3/judged.jsonl"):
    seen = {json.loads(x)["run"] for x in open("c3/judged.jsonl")}
out = open("c3/judged.jsonl", "a")
for r in rows:
    if r["run"] in seen:
        continue
    q = qs[r["q"]]
    answer = json.load(open(f"c3/runs/{r['run']}.json"))["answer"]
    last = answer.rsplit("답:", 1)[-1].strip()[:300] if "답:" in answer else answer.strip()[-300:]
    if r["status"] != "answered" or not last:
        v = {"verdict": "한도", "reason": r["status"]}
    else:
        gold = " / ".join(q["answers"]) if q["answers"] else "자료에 없음"
        ev = " ".join(q["evidence"])[:600]
        prompt = PROMPT.format(q=q["question"], gold=gold, ev=ev, a=last)
        m = ask([{"role": "user", "content": prompt}], None).choices[0].message.content
        try:
            v = json.loads(m[m.index("{") : m.rindex("}") + 1])
        except ValueError:
            v = {"verdict": "읽지 못함", "reason": m[:100]}
    if q["answers"] == [] and v["verdict"] == "모름":  # 자료에 없는 문항: 모른다고 하면 맞음
        v["verdict"] = "맞음"
    rec = {"run": r["run"], "q": r["q"], "last": last, **v}
    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out.flush()
print("채점 끝", len(rows))
