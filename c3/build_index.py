"""집합 하나의 BM25 색인을 디스크(SQLite FTS5)에 만든다. 실행: python c3/build_index.py 10k|100k|all
한국어를 나누는 방법은 앞에서 쓴 Kiwi 형태소 그대로다.
바뀐 건 저장하는 곳(메모리 → 디스크 파일)뿐이다.
제목과 본문을 다른 칸에 넣어서, 찾을 때 제목에 맞은 낱말에 점수를 더 줄 수 있게 한다."""

import sqlite3
import sys
import time

from kiwipiepy import Kiwi

SET = sys.argv[1]
BATCH = 2000
kiwi = Kiwi()


def words(tokens):  # 형태소 가운데 뜻 있는 말만(이름·움직임·숫자와 영어)
    return " ".join(t.form.lower() for t in tokens if t.tag[0] in "NVS")


db = sqlite3.connect("wiki/docs.db")
where = {"10k": "WHERE in10k=1", "100k": "WHERE in100k=1", "all": ""}[SET]
rows = db.execute(f"SELECT id, path, title FROM docs {where} ORDER BY id").fetchall()
db.execute(f"DROP TABLE IF EXISTS fts_{SET}")
# 원문은 파일에 있으니 색인만 저장
db.execute(f"CREATE VIRTUAL TABLE fts_{SET} USING fts5(title, body, content='')")

t0, chars = time.time(), 0
for b in range(0, len(rows), BATCH):
    part = rows[b : b + BATCH]
    texts = [open(f"wiki/{SET}/{p}", encoding="utf-8").read() for _, p, _ in part]
    chars += sum(len(t) for t in texts)
    bodies = kiwi.tokenize(texts)
    titles = kiwi.tokenize([t for _, _, t in part])
    db.executemany(
        f"INSERT INTO fts_{SET}(rowid, title, body) VALUES (?,?,?)",
        ((i, words(tt), words(bb)) for (i, _, _), tt, bb in zip(part, titles, bodies)),
    )
    if b % 50_000 == 0:
        print(f"{b:,}/{len(rows):,} · {time.time() - t0:.0f}초", flush=True)
db.commit()
print(f"{SET}: 문서 {len(rows):,}개 · 글자 {chars:,}자 · {time.time() - t0:.0f}초")
