import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

load_dotenv()
llm = OpenAI()
docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d, c) for d in docs for c in split(d["text"], 500, 100)]
OUT = "k8s/ctx_ko.json"
done = json.load(open(OUT)) if os.path.exists(OUT) else {}
ASK = """<document>
제목: {title}
{head}
</document>
다음은 위 문서에서 잘라 낸 청크입니다.
<chunk>
{chunk}
</chunk>
검색이 잘 되도록, 이 청크가 문서 안에서 무엇에 대한 내용인지 한두 문장으로 짧게 설명하세요. 설명만 출력하세요."""


def context(i):  # 청크 하나에 맥락 한두 문장 (문서 전체 대신 제목 + 앞부분 1,500자만 넣은 축소판)
    d, c = chunks[i]
    r = llm.chat.completions.create(model=os.environ["MODEL"], temperature=0,
                                    messages=[{"role": "user", "content": ASK.format(title=d["title"], head=d["text"][:1500], chunk=c)}])
    return i, r.choices[0].message.content.strip(), r.usage.prompt_tokens, r.usage.completion_tokens


todo = [i for i in range(len(chunks)) if str(i) not in done]
tokens = [0, 0]
with ThreadPoolExecutor(8) as pool:
    for n, (i, text, p, c) in enumerate(pool.map(context, todo)):
        done[str(i)] = text
        tokens[0] += p
        tokens[1] += c
        if n % 200 == 0:
            print(n, "/", len(todo), text[:60])
            json.dump(done, open(OUT, "w"), ensure_ascii=False)
json.dump(done, open(OUT, "w"), ensure_ascii=False)
print("청크", len(done), "· 입력 토큰", tokens[0], "· 출력 토큰", tokens[1])
