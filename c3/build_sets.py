"""위키 문서 폴더에서 포개진 세 집합(1만 ⊂ 10만 ⊂ 전체)을 만든다. 실행: python c3/build_sets.py <원본 문서 폴더>
- 문서 번호: 전체 경로를 정렬한 순서 그대로 w000000, w000001, … 파일 이름 앞에 붙인다.
- 질문의 근거 문서는 가장 작은 집합에도 반드시 들어간다. 나머지는 고정된 시드로 섞은 순서의 앞에서부터 채운다.
- 파일은 복사하지 않고 하드 링크로 만든다(원본과 같은 볼륨이어야 한다. 안 되면 복사)."""
import json
import os
import random
import shutil
import sqlite3
import sys

SRC = sys.argv[1].rstrip("/")
OUT = "wiki"
SIZES = {"10k": 10_000, "100k": 100_000}
SEED = 20261116

paths = sorted(f"{s}/{f}" for s in sorted(os.listdir(SRC)) if os.path.isdir(f"{SRC}/{s}") for f in os.listdir(f"{SRC}/{s}") if f.endswith(".txt"))
num = {p: i for i, p in enumerate(paths)}
print("문서", len(paths))

core = set()  # 질문 파일에 적힌 근거 문서
for q in json.load(open("c3/questions_src.json")):
    core.update(num[p] for p in q["docs"])
rest = [i for i in range(len(paths)) if i not in core]
random.Random(SEED).shuffle(rest)
sets = {name: set(core) | set(rest[: n - len(core)]) for name, n in SIZES.items()}
assert sets["10k"] <= sets["100k"]


def name(i):  # 618/짱구는_….txt → 618/w412345_짱구는_….txt
    shard, f = paths[i].split("/", 1)
    return f"{shard}/w{i:06d}_{f}"


def link(i, folder):
    dst = f"{OUT}/{folder}/{name(i)}"
    if os.path.exists(dst):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        os.link(f"{SRC}/{paths[i]}", dst)
    except OSError:  # 다른 볼륨이거나 하드 링크를 못 쓰는 파일 시스템
        shutil.copyfile(f"{SRC}/{paths[i]}", dst)


for i in range(len(paths)):
    link(i, "all")
    for s in sets:
        if i in sets[s]:
            link(i, s)

db = sqlite3.connect(f"{OUT}/docs.db")
db.execute("DROP TABLE IF EXISTS docs")
db.execute("CREATE TABLE docs (id INTEGER PRIMARY KEY, path TEXT, title TEXT, in10k INTEGER, in100k INTEGER)")
db.executemany("INSERT INTO docs VALUES (?,?,?,?,?)",
               ((i, name(i), paths[i].split("/", 1)[1][:-4].replace("_", " "), int(i in sets["10k"]), int(i in sets["100k"])) for i in range(len(paths))))
db.commit()

qs = []  # 질문 파일의 근거 경로를 문서 번호로 바꿔 저장
for q in json.load(open("c3/questions_src.json")):
    qs.append({**{k: v for k, v in q.items() if k != "docs"}, "docs": [f"w{num[p]:06d}" for p in q["docs"]]})
json.dump(qs, open("c3/questions.json", "w"), ensure_ascii=False, indent=1)
print({s: len(v) for s, v in sets.items()}, "근거 문서", len(core))
