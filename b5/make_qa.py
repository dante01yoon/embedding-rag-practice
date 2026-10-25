import json
import os
import random
import sys

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
LANG = sys.argv[1] if len(sys.argv) > 1 else "ko"
docs = json.load(open(f"k8s/docs_{LANG}.json"))
chunks = [{"path": d["path"], "text": c} for d in docs for c in split(d["text"], 500, 100) if len(c) > 300]
random.seed(0)
picked = random.sample(chunks, 40)  # 문서 청크 40개를 무작위로 고른다

ASK = {"ko": "아래 글만 읽고 답할 수 있는 질문을 하나 만드세요. 쿠버네티스를 쓰는 사람이 실제로 물어볼 법한 말투로, 글의 문장을 그대로 베끼지 말고 한 문장으로. 질문만 출력하세요.",
       "en": "Write one question that can be answered only from the text below. Phrase it the way a real Kubernetes user would ask, in one sentence, without copying sentences from the text. Output only the question."}
with open(f"k8s/qa_{LANG}.jsonl", "w") as f:
    for c in picked:
        q = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": f"{ASK[LANG]}\n\n{c['text']}"}])
        row = {"question": q.choices[0].message.content.strip(), "path": c["path"], "source": c["text"][:200]}  # 정답 = 이 청크가 나온 문서
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(row["question"], "→", row["path"].split("/", 2)[2])
print("저장:", f"k8s/qa_{LANG}.jsonl")
