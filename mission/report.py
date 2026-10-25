import json
import os
import sys
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
docs = json.load(open("k8s/docs_ko.json"))  # 내 문서 자리: 쿠버네티스 한국어 문서 155개
title = {d["path"]: d["title"] for d in docs}
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
qa = json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json"))  # 골든셋 78개
model = SentenceTransformer("BAAI/bge-m3")
PROMPT = "아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
JUDGE = "자료:\n{ctx}\n\n답:\n{a}\n\n답의 모든 내용이 자료로 뒷받침되면 '예', 자료에 없는 내용이 하나라도 있으면 '아니오'라고만 답하세요."
PRICE_IN, PRICE_OUT = 0.10, 0.50  # 달러 / 100만 토큰 (OpenRouter claude-haiku-5.5 가격표, 2026-10)


def chat(prompt):
    r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
    return r.choices[0].message.content.strip(), r.usage.prompt_tokens, r.usage.completion_tokens


rows = []
for x in qa:
    t0 = time.time()
    top = np.argsort(-(vecs @ model.encode(x["question"], normalize_embeddings=True)))[:4]
    t1 = time.time()
    ctx = "\n\n".join(chunks[i][1] for i in top)
    a, i, o = chat(PROMPT.format(ctx=ctx, q=x["question"]))
    t2 = time.time()
    ok = chat(JUDGE.format(ctx=ctx, a=a))[0].startswith("예")
    rows.append({"q": x["question"], "gold": x["path"], "top1": chunks[top[0]][0], "hit": x["path"] in {chunks[j][0] for j in top},
                 "faithful": ok, "refused": "자료에 없습니다" in a, "search": t1 - t0, "total": t2 - t0, "in": i, "out": o})


def ci(v, n=2000):  # 부트스트랩 95% 신뢰구간: 질문을 복원 추출로 다시 뽑아 평균을 n번 잰다
    v = np.array(v, float)
    m = np.random.default_rng(0).choice(v, (n, len(v))).mean(1)
    return v.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


R, F = ci([r["hit"] for r in rows]), ci([r["faithful"] for r in rows if not r["refused"]])  # 거절은 충실성에서 빼고 따로 센다
sec = np.array([r["total"] for r in rows])
cost = sum(r["in"] * PRICE_IN + r["out"] * PRICE_OUT for r in rows) / 1e6 / len(rows)
miss = [r for r in rows if not r["hit"]][:3]
lines = ["# 평가 리포트", "", f"질문 {len(rows)}개 · 청크 {len(chunks):,}개 · 상위 4개", "", "| 지표 | 값 | 95% 신뢰구간 |", "|---|---|---|",
         f"| 검색 Recall@4 | {R[0]:.1%} | {R[1]:.1%} ~ {R[2]:.1%} |", f"| 답 충실성 | {F[0]:.1%} | {F[1]:.1%} ~ {F[2]:.1%} |",
         f"| 거절('자료에 없습니다') | {np.mean([r['refused'] for r in rows]):.1%} | 그중 정답 문서를 찾고도 거절 {sum(r['refused'] and r['hit'] for r in rows)}개 |", "", "## 지연·비용", "", "| p50 | p95 | 검색 평균 | 질문당 비용 | 하루 1만 번 |", "|---|---|---|---|---|",
         f"| {np.percentile(sec, 50):.2f}초 | {np.percentile(sec, 95):.2f}초 | {np.mean([r['search'] for r in rows]):.2f}초 | ${cost:.5f} | ${cost * 10000:.2f} |", "", "## 실패 사례 (검색이 정답 문서를 못 찾은 질문)", ""]
lines += [f"{k + 1}. {r['q']}  \n   정답: {title[r['gold']]} · 1위로 찾은 문서: {title[r['top1']]}" for k, r in enumerate(miss)]
json.dump(rows, open("mission/rows.json", "w"), ensure_ascii=False)
open("mission/REPORT.md", "w").write("\n".join(lines) + "\n")
print(f"Recall@4 {R[0]:.1%} [{R[1]:.1%}~{R[2]:.1%}] · 충실성 {F[0]:.1%} [{F[1]:.1%}~{F[2]:.1%}] · p95 {np.percentile(sec, 95):.2f}초 · 질문당 ${cost:.5f}")
print("저장: mission/REPORT.md")
