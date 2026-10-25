import json
import os
import re
import sys

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, "b3x")
from strategies import BUDGET, cover, model, norm, qa, sentences  # noqa: E402

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_b3x.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = [r.choices[0].message.content.strip(), r.usage.prompt_tokens]
    return cache[prompt]


docs = json.load(open("k8s/docs_ko.json"))
PROMPT = ("아래는 번호를 붙인 문서의 문장들입니다. 주제가 바뀌는 곳에서 묶음을 나누세요. 한 묶음은 대략 300~900자입니다.\n"
          "각 묶음이 시작하는 문장 번호만 쉼표로 출력하세요. 예: 0, 7, 15\n\n{body}")


def agentic(text):  # LLM이 주제가 바뀌는 곳을 골라 자른다
    ss = sentences(text)
    if not ss:
        return [], 0
    answer, tokens = ask(PROMPT.format(body="\n".join(f"[{i}] {s}" for i, s in enumerate(ss))))
    starts = sorted({int(n) for n in re.findall(r"\d+", answer) if int(n) < len(ss)} | {0})
    return [" ".join(ss[a:b]) for a, b in zip(starts, starts[1:] + [len(ss)])], tokens


units, tokens = [], 0
for d in docs:
    cs, t = agentic(d["text"])
    units += cs
    tokens += t
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
vecs = model.encode(units, normalize_embeddings=True, batch_size=32)
hit, fair, size = 0, 0, []
for x in qa:
    order = np.argsort(-(vecs @ model.encode(x["question"], normalize_embeddings=True)))[:50]
    ctx = "".join(units[i] for i in order[:4])
    hit += norm(x["source"][:60]) in norm(ctx)
    size.append(len(ctx))
    fair += cover(x["source"], "".join(units[i] for i in order)[:BUDGET])
print(f"에이전트(LLM이 경계 결정) | 청크 {len(units):5,}개 · 처음 기준 {hit}/{len(qa)} (평균 {np.mean(size):5,.0f}자) · 정답 문장 {fair / len(qa) * 100:4.1f}% · LLM 입력 {tokens:,}토큰")
