"""도구만 직접 불러 보기(모델을 부르지 않는다). 실행: python -i c3/try_tools.py [10k|100k|all] [pull]
파이썬 창(>>>)이 열리면 find("닛폰햄"), find("1975년", within="r1"), read("w199008", at="월간 타율")처럼 부른다.
에이전트가 부를 때와 같은 Box.call을 거친다. 화면에 맞춰 줄여서 보여 준다:
긴 줄은 낱말 사이에서 나누고, 문서가 세 개 넘으면 번호와 제목만, 줄이 많으면 앞부분만. clear()는 화면을 비운다.
끝에 pull을 붙이면 끌어와서 뒤지기 방식(빈 작업 폴더)으로 열리고 pull("검색어", k=50)을 쓸 수 있다."""

import sys
import unicodedata

sys.path.insert(0, "c3")
from tools import Box  # noqa: E402

SET = sys.argv[1] if len(sys.argv) > 1 else "10k"
MODE = sys.argv[2] if len(sys.argv) > 2 else "raw"
box = Box(SET, MODE)
WIDTH, ROWS, FULL = 82, 13, 3  # 한 줄의 칸 수, 호출 하나에 보여 주는 줄 수, 발췌까지 보여 주는 문서 수


def width(text):  # 한글은 두 칸
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def rows(line):  # 긴 줄을 화면 폭에 맞춰 낱말 사이에서 나눈다
    out, cur = [], ""
    for word in line.split(" "):
        if cur and width(cur) + 1 + width(word) > WIDTH:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    return out + [cur]


def show(out):
    lines = out.split("\n")
    if sum(" | …" in x for x in lines) > FULL:  # 문서가 많으면 번호와 제목만
        lines = [x.split(" | …")[0] for x in lines]
    part = [r for line in lines for r in rows(line)]
    cut = ROWS if len(part) > ROWS + 1 else len(part)
    print("\n".join("  " + r for r in part[:cut]))
    if cut < len(part):
        print(f"     ⋮ {len(part) - cut}줄 더")


def find(pattern, **args):
    show(box.call("find", {"pattern": pattern, **args}))


def read(doc_id, **args):
    show(box.call("read", {"doc_id": doc_id, **args}))


def pull(query, **args):
    show(box.call("pull", {"query": query, **args}))


def clear():
    print("\033[H\033[2J\033[3J", end="")


if MODE == "pull":
    print(f'  Box("{SET}", "pull") · pull(검색어, k=) · find(패턴, within=) · read(문서 번호, at=) · clear()')
else:
    print(f'  Box("{SET}") · find(패턴, within=, offset=) · read(문서 번호, at=, offset=) · clear()')
