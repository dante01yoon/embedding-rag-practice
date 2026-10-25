import json
import os

import httpx
import numpy as np
import redis

qa = json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json"))  # 골든셋 78개
PRICE_IN, PRICE_OUT = 0.10, 0.50  # 달러 / 100만 토큰 (OpenRouter claude-haiku-5.5 가격표, 2026-10)
ALERT = 0.5  # 같은 질문인데 히트율이 이보다 낮으면 알림
api = httpx.Client(base_url="http://127.0.0.1:8001", timeout=60)
cache = redis.Redis(port=6380)

for run in ["첫 번째", "같은 질문 다시"]:
    if run == "같은 질문 다시" and os.environ.get("KEY_CHANGE"):  # 연습: 그사이 캐시 키가 바뀌었다 (모델·프롬프트·색인 교체처럼)
        cache.incr("index:version")
    rows = [api.get("/ask", params={"q": x["question"]}).json() | {"gold": x["path"]} for x in qa]
    sec = np.array([r["sec"] for r in rows])
    recall = np.mean([r["gold"] in r["paths"] for r in rows])
    cost = sum(0 if r["cached"] else r["in"] * PRICE_IN + r["out"] * PRICE_OUT for r in rows) / 1e6 / len(rows)
    hit = np.mean([r["cached"] for r in rows])
    print(f"{run:<8} | Recall@4 {recall:.1%} · p50 {np.percentile(sec, 50):.2f}초 · p95 {np.percentile(sec, 95):.2f}초 · 질문당 ${cost:.5f} · 캐시 히트 {hit:.0%}")
    if run == "같은 질문 다시" and hit < ALERT:
        print(f"  알림: 같은 질문인데 캐시 히트율 {hit:.0%} < {ALERT:.0%} · 에러는 없고 비용만 든다 → 캐시 키가 바뀌었는지 확인")
