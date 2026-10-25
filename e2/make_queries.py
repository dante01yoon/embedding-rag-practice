import csv
import json
import os
import random

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
llm = OpenAI()
CACHE = "books/llm_cache_e2.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
books = [r for r in csv.DictReader(open("books/books_mood.csv")) if r["title"].strip() and len(r["description"]) > 80]
random.seed(7)
pick = random.sample(books, 60)


def typo(t):  # 두 글자 바꾸기 / 한 글자 빼기 / 한 글자 반복 중 하나
    t = list(t.replace(" ", ""))
    i = random.randrange(max(1, len(t) - 1))
    k = random.choice(["swap", "drop", "dup"]) if len(t) > 2 else "dup"
    if k == "swap":
        t[i], t[i + 1] = t[i + 1], t[i]
    elif k == "drop":
        del t[i]
    else:
        t.insert(i, t[i])
    return "".join(t)


P = "다음 책을 찾는 사람이 검색창에 칠 법한 짧은 묘사형 검색어를 하나만 쓰세요. 제목과 작가 이름의 낱말은 쓰지 마세요. 검색어만 출력하세요.\n\n제목: {t}\n작가: {a}\n소개: {d}"
qs = []
for b in pick:
    qs.append({"q": typo(b["title"]), "kind": "오타", "id": b["pageid"]})
    p = P.format(t=b["title"], a=b["author"], d=b["description"][:300])
    if p not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": p}], temperature=0)
        cache[p] = r.choices[0].message.content.strip().strip('"')
    qs.append({"q": cache[p], "kind": "묘사", "id": b["pageid"]})
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
json.dump(qs, open("books/queries_e2.json", "w"), ensure_ascii=False, indent=1)
for x in qs[:6]:
    print(x)
