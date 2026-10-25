import difflib
import json
import os
import re
import sys

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], d["title"], c) for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
model = SentenceTransformer("BAAI/bge-m3")
CACHE = "k8s/llm_cache_b7.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


def context(q):
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:4]
    return "\n\n".join(f"[{n + 1}] {chunks[i][1]}\n{chunks[i][2]}" for n, i in enumerate(top))


NOANS = "자료에 없습니다."
STRICT = "아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 답이 없으면 '" + NOANS + "'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
PLAIN = "아래 자료를 참고해 질문에 답하세요.\n\n{ctx}\n\n질문: {q}"
BREAK = "다음 답에서 사실 하나만 그럴듯하게 틀리게 바꿔 주세요. 숫자, 이름, 동작 중 하나를 바꾸고 나머지는 그대로 두세요. 바꾼 답만 출력하세요.\n\n{a}"
JUDGE = "아래 자료와 답을 비교하세요. 답의 문장 중 하나라도 자료로 확인되지 않으면 '근거 없음', 모두 확인되면 '충실'이라고만 답하세요.\n\n자료:\n{ctx}\n\n답: {a}"


def judge(ctx, a):  # LLM 심판: 근거 없는 문장이 있으면 True
    return "근거 없음" in ask(JUDGE.format(ctx=ctx, a=a))


def bare(a):  # 근거 번호를 빼고 본문만
    return re.sub(r"\s*\[\d\]", "", a).strip()


rows = []
for item in json.load(open("k8s/qa_ko_reviewed.json"))[:15]:
    ctx = context(item["question"])
    good = ask(STRICT.format(ctx=ctx, q=item["question"]))  # 지난 수업의 엄격한 답 = 맞는 답
    if NOANS in good:
        continue
    bad = ask(BREAK.format(a=good))  # 일부러 사실 하나를 틀리게 만든 답 = 오답
    rows.append((ctx, good, bad, ask(PLAIN.format(ctx=ctx, q=item["question"]))))
real = [r for r in rows if bare(r[1]) != bare(r[2])]  # 본문이 실제로 바뀐 오답만
print(f"오답 만들기: {len(rows)}개 중 실제로 바뀐 것 {len(real)}개")
caught = sum(judge(c, b) for c, g, b, p in real)
alarm = sum(judge(c, g) for c, g, b, p in rows)
flag = sum(judge(c, p) for c, g, b, p in rows)
print(f"심판 | 오답 잡음 {caught}/{len(real)} · 맞는 답을 근거 없음이라 함 {alarm}/{len(rows)} · '그냥' 답 근거 없음 {flag}/{len(rows)}")
for c, g, b, p in real:
    if not judge(c, b):
        print("놓침:", " ".join(w for w in difflib.ndiff(g.split(), b.split()) if w[0] in "+-")[:120])
json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
