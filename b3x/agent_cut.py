import json
import os
import re

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()
llm = OpenAI()
CACHE = "k8s/llm_cache_b3x.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):  # 답과 입력 토큰을 함께 저장
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = [r.choices[0].message.content.strip(), r.usage.prompt_tokens]
    return cache[prompt]


docs = json.load(open("k8s/docs_ko.json"))
qa = json.load(open("k8s/qa_sent.json"))  # 원문 문장에서 뽑은 공정한 질문 80개
model = SentenceTransformer("BAAI/bge-m3")
norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731


def sentences(t):
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)
    return [s.strip() for s in re.split(r"(?<=[.다?!])\s+|\n\n+", t) if s.strip()]


SIZE = "200~500"  # LLM에게 부탁할 묶음 크기
PROMPT = "아래는 번호를 붙인 문서의 문장들입니다. 주제가 바뀌는 곳에서 묶음을 나누세요. 한 묶음은 대략 {size}자입니다.\n각 묶음이 시작하는 문장 번호만 쉼표로 출력하세요. 예: 0, 7, 15\n\n{body}"


def agentic(text):  # LLM이 문장 번호를 보고 주제가 바뀌는 곳을 고른다
    ss = sentences(text)
    if not ss:
        return [], 0
    answer, tokens = ask(PROMPT.format(size=SIZE, body="\n".join(f"[{i}] {s}" for i, s in enumerate(ss))))
    starts = sorted({int(n) for n in re.findall(r"\d+", answer) if int(n) < len(ss)} | {0})
    return [" ".join(ss[a:b]) for a, b in zip(starts, starts[1:] + [len(ss)])], tokens


units, tokens = [], 0
for d in docs:
    cs, t = agentic(d["text"])
    units += cs
    tokens += t
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
vecs = model.encode(units, normalize_embeddings=True, batch_size=32)
got = []
for x in qa:
    order = np.argsort(-(vecs @ model.encode(x["question"], normalize_embeddings=True)))[:50]
    ctx = "".join(units[i] for i in order)[:2000]  # 재귀와 같은 2,000자
    got.append(norm(x["source"]) in norm(ctx))
print(f"에이전트 {SIZE}자 | 청크 {len(units):,}개 · 평균 {np.mean([len(u) for u in units]):,.0f}자 · 정답 문장 {np.mean(got) * 100:4.1f}% · LLM 입력 {tokens:,}토큰")
