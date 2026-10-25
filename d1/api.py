import json
import os
import sys
import time

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
docs = json.load(open("k8s/docs_ko.json"))
chunks = [c for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
model = SentenceTransformer("BAAI/bge-m3")  # 서버가 뜰 때 한 번만 읽는다
PROMPT = "아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}"
app = FastAPI()


@app.get("/ask")
def ask(q: str):
    t0 = time.time()
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:4]
    t1 = time.time()
    r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": PROMPT.format(ctx="\n\n".join(chunks[i] for i in top), q=q)}], temperature=0)
    return {"answer": r.choices[0].message.content, "in": r.usage.prompt_tokens, "out": r.usage.completion_tokens,
            "search_sec": round(t1 - t0, 2), "llm_sec": round(time.time() - t1, 2)}
