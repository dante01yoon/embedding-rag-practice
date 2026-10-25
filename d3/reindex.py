import copy
import hashlib
import json
import sys
import time

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

model = SentenceTransformer("BAAI/bge-m3")


def pieces(docs):  # 청크 이름 = 문서 경로 + 내용 해시 → 내용이 같으면 이름도 같다
    return [(f"{d['path']}#{hashlib.sha1(c.encode()).hexdigest()[:10]}", d["path"], c) for d in docs for c in split(d["text"], 500, 100)]


old = json.load(open("k8s/docs_ko.json"))
index = {k: (p, c, v) for (k, p, c), v in zip(pieces(old), np.load("k8s/vecs_ko_500.npy"))}  # 어제 만든 색인

new = copy.deepcopy(old)  # 오늘의 문서: 하나 고치고, 하나 지우고, 하나 추가 (연습용 변경)
for d in new:
    if d["path"].endswith("configmap.md"):
        d["text"] = d["text"].replace("1MiB를 초과할 수 없다", "2MiB를 초과할 수 없다")
new = [d for d in new if not d["path"].endswith("cgroups.md")]
new.append({"path": "k8s/ko/notice/maintenance.md", "title": "점검 공지", "text": "[연습용 공지] 다음 클러스터 정기 점검은 11월 4일 화요일 새벽 2시에 진행한다. 점검 중에는 새 파드를 배포할 수 없다."})

now = {k: (p, c) for k, p, c in pieces(new)}
add = [k for k in now if k not in index]
t = time.time()
vecs = model.encode([now[k][1] for k in add], normalize_embeddings=True)
index.update({k: (*now[k], v) for k, v in zip(add, vecs)})
gone = [k for k in index if k not in now]  # 오늘 문서에 없는 청크
for k in gone:
    del index[k]
print(f"오늘 청크 {len(now):,}개 · 새로 임베딩 {len(add)}개 · {time.time() - t:.1f}초 · 지운 청크 {len(gone)}개 · 색인 {len(index):,}개")


def search(q, k=4):  # 상위 청크 k개 (문서 경로, 내용)
    keys = list(index)
    s = np.stack([index[x][2] for x in keys]) @ model.encode(q, normalize_embeddings=True)
    return [index[keys[i]][:2] for i in np.argsort(-s)[:k]]


top = search("컨피그맵에 저장할 수 있는 데이터 한도는?")
print(f"컨피그맵 한도 → 상위 청크 4개 중 '1MiB' {sum('1MiB' in c for _, c in top)}개 · '2MiB' {sum('2MiB' in c for _, c in top)}개")
for q in ["cgroup v2는 무엇인가요?", "다음 클러스터 점검은 언제인가요?"]:
    print(f"{q} → 1위 {search(q)[0][0].split('/')[-1]}")
