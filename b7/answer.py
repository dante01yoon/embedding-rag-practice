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


def context(q):  # 질문과 가까운 청크 4개에 번호를 붙여 이어 붙인다
    top = np.argsort(-(vecs @ model.encode(q, normalize_embeddings=True)))[:4]
    return "\n\n".join(f"[{n + 1}] {chunks[i][1]}\n{chunks[i][2]}" for n, i in enumerate(top))


NOANS = "자료에 없습니다."  # 거절할 때 쓸 정해진 문장
PROMPTS = {
    "그냥": "아래 자료를 참고해 질문에 답하세요.\n\n{ctx}\n\n질문: {q}",
    "엄격": "아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 답이 없으면 '" + NOANS + "'라고만 답하세요.\n\n{ctx}\n\n질문: {q}",
}
NO = ["도커 데스크톱 유료 요금제는 한 달에 얼마예요?", "AWS EKS 클러스터는 한 시간에 요금이 얼마예요?", "쿠버네티스 공식 마스코트 이름은 뭐예요?",
      "쿠버네티스를 처음 만든 사람의 고향은 어디예요?", "구글 클라우드에서 GKE 오토파일럿 무료 사용량은 얼마예요?"]  # 문서에 답이 없는 질문
YES = [x["question"] for x in json.load(open("k8s/qa_ko_reviewed.json"))[:5]]  # 문서에 답이 있는 질문

for name, tmpl in PROMPTS.items():
    no = [ask(tmpl.format(ctx=context(q), q=q)) for q in NO]
    yes = [ask(tmpl.format(ctx=context(q), q=q)) for q in YES]
    refused = sum(NOANS in a for a in no)
    cited = sum(bool(re.search(r"\[\d\]", a)) for a in yes)
    print(f"{name} | 답 없는 질문: 거절 {refused}/{len(no)} · 평균 {np.mean([len(a) for a in no]):.0f}자 | 답 있는 질문: 근거 번호 {cited}/{len(yes)} · 잘못 거절 {sum(NOANS in a for a in yes)}/{len(yes)}")
print("\n[그냥] " + ask(PROMPTS["그냥"].format(ctx=context(NO[1]), q=NO[1]))[:300])
json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
