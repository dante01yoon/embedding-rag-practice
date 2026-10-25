import json
import sys
import time

import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, "d1")
from api import app  # noqa: E402

client = TestClient(app)  # 서버를 띄운 것처럼 HTTP로 부른다
QS = [x["question"] for x in json.load(open("k8s/qa_ko_short.json"))][:20]
PRICE_IN, PRICE_OUT = 0.10, 0.50  # 달러 / 100만 토큰 (OpenRouter claude-haiku-5.5 가격표, 2026-10)

rows = []
for q in QS:
    t = time.time()
    r = client.get("/ask", params={"q": q}).json()
    rows.append((time.time() - t, r["search_sec"], r["llm_sec"], r["in"], r["out"]))
sec = np.array([x[0] for x in rows])
print(f"질문 {len(rows)}개 | p50 {np.percentile(sec, 50):.2f}초 · p95 {np.percentile(sec, 95):.2f}초 · 검색 평균 {np.mean([x[1] for x in rows]):.2f}초 · LLM 평균 {np.mean([x[2] for x in rows]):.2f}초")
cost = sum(i * PRICE_IN + o * PRICE_OUT for *_, i, o in rows) / 1e6 / len(rows)
print(f"질문당 입력 {np.mean([x[3] for x in rows]):,.0f} · 출력 {np.mean([x[4] for x in rows]):,.0f}토큰 · 비용 ${cost:.5f} · 하루 1만 번이면 ${cost * 10000:.2f}")
