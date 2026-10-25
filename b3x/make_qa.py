import json
import os
import random
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, "b3x")
from strategies import docs, sentences  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_b3x.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
PROMPT = "아래 문장 하나로 답할 수 있는 짧은 질문을 한국어로 하나만 쓰세요. 문장의 표현을 그대로 베끼지 말고, 사용자가 실제로 물을 법한 말로 쓰세요. 질문만 출력하세요.\n\n문장: {s}"

random.seed(0)
pool = [(d["path"], s) for d in docs for s in sentences(d["text"])
        if 40 <= len(s) <= 200 and not re.search(r"[`{}<>|=#\[\]]|\s{3,}|\w+: \w+", s)]  # 코드·표·링크가 없는 평범한 문장
qa = []
for path, s in random.sample(pool, 80):  # 어떤 자르기와도 상관없이 원문에서 고른 정답 문장
    p = PROMPT.format(s=s)
    if p not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": p}], temperature=0)
        cache[p] = [r.choices[0].message.content.strip(), r.usage.prompt_tokens]
    qa.append({"question": cache[p][0], "path": path, "source": s})
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
json.dump(qa, open("k8s/qa_sent.json", "w"), ensure_ascii=False, indent=1)
print(len(pool), len(qa))
for x in qa[:3]:
    print(x["question"], "←", x["source"][:60])
