"""수집 자동화 실습 준비: 문서 폴더(d9/docs)와 어제까지의 색인·상태를 만든다. (녹화 전 한 번)"""
import hashlib
import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

shutil.rmtree("d9/docs", ignore_errors=True)
os.makedirs("d9/docs")
docs = json.load(open("k8s/docs_ko.json"))
keys, state = [], {}
for d in docs:
    f = "d9/docs/" + d["path"].removeprefix("k8s/ko/").replace("/", "__")
    open(f, "w").write(f"# {d['title']}\n\n{d['text']}")
    os.utime(f, (1790000000, 1790000000))  # 어제 수집한 시각
    state[f] = {"mtime": 1790000000, "hash": hashlib.sha1(open(f, "rb").read()).hexdigest()}
    keys += [[f, c] for c in split(d["text"], 500, 100)]
json.dump(keys, open("d9/index.json", "w"), ensure_ascii=False)
np.save("d9/vecs.npy", np.load("k8s/vecs_ko_500.npy"))
json.dump({"last_run": 1790000000, "files": state}, open("d9/state.json", "w"))
print(f"문서 {len(docs)}개 · 청크 {len(keys):,}개")
