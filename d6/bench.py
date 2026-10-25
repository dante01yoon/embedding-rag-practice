import json

import httpx
import numpy as np

qa = json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json"))  # 골든셋 78개
PRICE_IN, PRICE_OUT = 0.10, 0.50  # 달러 / 100만 토큰 (OpenRouter claude-haiku-5.5 가격표, 2026-10)
api = httpx.Client(base_url="http://127.0.0.1:8001", timeout=60)

for run in ["첫 번째", "같은 질문 다시"]:
    rows = [api.get("/ask", params={"q": x["question"]}).json() | {"gold": x["path"]} for x in qa]
    sec = np.array([r["sec"] for r in rows])
    recall = np.mean([r["gold"] in r["paths"] for r in rows])
    cost = sum(0 if r["cached"] else r["in"] * PRICE_IN + r["out"] * PRICE_OUT for r in rows) / 1e6 / len(rows)
    hit = np.mean([r["cached"] for r in rows])
    print(f"{run:<8} | Recall@4 {recall:.1%} · p50 {np.percentile(sec, 50):.2f}초 · p95 {np.percentile(sec, 95):.2f}초 · 질문당 ${cost:.5f} · 캐시 히트 {hit:.0%}")
