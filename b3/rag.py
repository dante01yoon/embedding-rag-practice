import json
import os
import sys
import textwrap

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()
chunks = json.load(open("k8s/chunks.json"))  # index.py가 만든 청크와 벡터
vecs = np.load("k8s/index.npy")
embed = SentenceTransformer("BAAI/bge-m3")
llm = OpenAI()


def retrieve(question, k=4):  # 1) 검색: 질문과 가까운 청크 k개
    q = embed.encode(question, normalize_embeddings=True)
    return [chunks[i] for i in np.argsort(-(vecs @ q))[:k]]


def answer(question):
    found = retrieve(question)
    context = "\n\n".join(f"[{i + 1}] {c['title']}\n{c['text']}" for i, c in enumerate(found))  # 2) 청크에 번호를 붙여 이어 붙인다
    prompt = (f"아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 없으면 모른다고 답하세요.\n\n"
              f"{context}\n\n질문: {question}")
    reply = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}])  # 3) 생성
    for line in ("답: " + reply.choices[0].message.content).splitlines():
        print(textwrap.fill(line, 60))  # 터미널에서 읽기 좋게 60자마다 줄바꿈
    for i, c in enumerate(found):
        print(f"  [{i + 1}] {c['title']} · {c['path']}")


answer(sys.argv[1] if len(sys.argv) > 1 else "파드 안의 컨테이너들은 무엇을 함께 쓰나요?")
