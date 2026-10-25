import hashlib
import json
import os
import time

import psycopg
import redis
from fastapi import FastAPI
from openai import OpenAI
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

llm = OpenAI()
db = psycopg.connect(os.environ["DB"], autocommit=True)
db.execute("CREATE EXTENSION IF NOT EXISTS vector")  # 새 DB면 벡터 확장부터 (적재보다 API가 먼저 뜰 수 있다)
register_vector(db)
cache = redis.Redis.from_url(os.environ["CACHE"])
model = SentenceTransformer("BAAI/bge-m3")
PROMPT = "아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
app = FastAPI()


@app.get("/ask")
def ask(q: str):
    t0 = time.time()
    ver = int(cache.get("index:version") or 0)
    key = f"ans:{ver}:" + hashlib.sha1(q.encode()).hexdigest()  # 캐시 키 = 색인 버전 + 질문의 지문
    if (hit := cache.get(key)) is not None:
        return {**json.loads(hit), "cached": True, "sec": round(time.time() - t0, 3)}
    rows = db.execute("SELECT path, body FROM chunks ORDER BY emb <=> %s LIMIT 4", (model.encode(q, normalize_embeddings=True),)).fetchall()
    r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": PROMPT.format(ctx="\n\n".join(b for _, b in rows), q=q)}], temperature=0)
    out = {"answer": r.choices[0].message.content, "paths": [p for p, _ in rows], "in": r.usage.prompt_tokens, "out": r.usage.completion_tokens}
    cache.set(key, json.dumps(out, ensure_ascii=False), ex=3600)  # 1시간 동안 기억
    return {**out, "cached": False, "sec": round(time.time() - t0, 3)}
