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
CACHE = "k8s/llm_cache_c1.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


docs = json.load(open("k8s/docs_ko.json"))
chunks = [c for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
model = SentenceTransformer("BAAI/bge-m3")
NO = ["도커 데스크톱 유료 요금제는 한 달에 얼마예요?", "AWS EKS 클러스터는 한 시간에 요금이 얼마예요?", "쿠버네티스 공식 마스코트 이름은 뭐예요?",
      "쿠버네티스를 처음 만든 사람의 고향은 어디예요?", "구글 클라우드에서 GKE 오토파일럿 무료 사용량은 얼마예요?"]  # 문서에 답이 없는 질문
QS = [x["question"] for x in json.load(open("k8s/qa_ko_short.json"))] + NO

PROMPTS = {
    "그냥": "아래 자료를 참고해 질문에 세 문장 이내로 답하세요.\n\n{ctx}\n\n질문: {q}",
    "엄격": "아래 자료에 나온 내용만으로 질문에 세 문장 이내로 답하세요. 자료에 없는 내용은 쓰지 말고, 답이 자료에 없으면 '자료에 없습니다.'라고만 답하세요.\n\n{ctx}\n\n질문: {q}",
}
JUDGE = "자료:\n{ctx}\n\n문장: {s}\n\n이 문장의 내용이 자료에 나와 있으면 '있음', 자료에 없는 내용이 들어 있으면 '없음'이라고만 답하세요. 자료에 없다고 밝히는 문장은 '있음'입니다."


def sentences(tmpl, q):  # 검색한 청크 4개로 답하고, 답을 문장으로 나눈다
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:4]
    ctx = "\n\n".join(chunks[i] for i in top)
    answer = ask(tmpl.format(ctx=ctx, q=q))
    return [(ctx, s.strip()) for s in re.split(r"(?<=[.다요])\s+", answer) if len(s.strip()) > 5]


for name, tmpl in PROMPTS.items():
    sents = [x for q in QS for x in sentences(tmpl, q)]
    bad = [s for ctx, s in sents if "있음" not in ask(JUDGE.format(ctx=ctx, s=s))]  # 자료에 없는 내용이 든 문장
    print(f"{name} | 근거 없는 문장 {len(bad)}/{len(sents)}")
    for s in bad[-2:]:
        print(f"   예) {s[:56]}")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
