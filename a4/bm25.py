import bm25s
from kiwipiepy import Kiwi

docs = open("a4/docs_ko.txt").read().splitlines()  # 한 줄 = 문서 하나
query = "강아지 사료"


def space(t):
    return t.split()  # 띄어쓰기로 자르기


def search(name, tok):
    index = bm25s.BM25()  # 기본값 k1=1.5, b=0.75
    index.index([tok(d) for d in docs], show_progress=False)
    ids, scores = index.retrieve([tok(query)], k=len(docs), show_progress=False)
    print(f"\n[{name}] 질문 조각: {tok(query)}")
    for i, s in zip(ids[0], scores[0]):
        print(f"  {s:.2f}  {docs[i]}  ← {tok(docs[i])}")


search("띄어쓰기", space)

kiwi = Kiwi()
KEEP = ("NN", "VV", "VA", "XR", "SL", "SN")  # 명사·동사·형용사·어근·외국어·숫자


def morph(t):
    return [x.form for x in kiwi.tokenize(t) if x.tag.startswith(KEEP)]  # 형태소


search("형태소", morph)
