import hashlib
import json
import os
import sys
import time

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

model = SentenceTransformer("BAAI/bge-m3")
state = json.load(open("d9/state.json"))  # 지난번 수집 기록: 파일마다 수정 시각·내용 해시
keys, vecs = json.load(open("d9/index.json")), np.load("d9/vecs.npy")  # 색인: [파일, 청크] + 벡터


def parse(f):  # 첫 줄 '# 제목' 떼고 본문만
    return open(f).read().split("\n", 1)[1].strip()


def embed(texts, tries=3):  # 실패하면 1초, 2초 기다렸다 다시 · 끝내 실패하면 예외
    for n in range(tries):
        try:
            if os.environ.get("CHAOS") and n == 0:  # 장애 연습: 첫 시도를 일부러 실패시킨다
                raise TimeoutError("임베딩 서버 응답 없음")
            return model.encode(texts, normalize_embeddings=True)
        except TimeoutError as e:
            if n == tries - 1:
                raise
            print(f"  재시도 {n + 1} · {e}")
            time.sleep(2 ** n)


t = time.time()
files = {f"d9/docs/{x}": hashlib.sha1(open(f"d9/docs/{x}", "rb").read()).hexdigest() for x in sorted(os.listdir("d9/docs"))}
changed = [f for f, h in files.items() if state["files"].get(f, {}).get("hash") != h]  # 내용 해시가 다르거나 새 파일
gone = [f for f in state["files"] if f not in files]
done, failed, embedded = 0, [], 0
for f in changed:
    old = {c: vecs[i] for i, (kf, c) in enumerate(keys) if kf == f}  # 이 파일의 옛 청크와 벡터
    try:
        new = split(parse(f), 500, 100)
        need = [c for c in new if c not in old]  # 내용이 같은 청크는 벡터를 다시 쓰고, 바뀐 청크만 임베딩
        made = dict(zip(need, embed(need))) if need else {}
    except Exception as e:  # 한 문서가 실패해도 나머지는 계속, 실패 목록에 남긴다
        failed.append((f, str(e)))
        continue
    keep = [i for i, (kf, _) in enumerate(keys) if kf != f]
    keys, vecs = [keys[i] for i in keep] + [[f, c] for c in new], np.vstack([vecs[keep]] + [old.get(c, made.get(c)) for c in new])
    state["files"][f] = {"mtime": os.path.getmtime(f), "hash": files[f]}
    done, embedded = done + 1, embedded + len(need)
keep = [i for i, (kf, _) in enumerate(keys) if kf not in gone]
keys, vecs = [keys[i] for i in keep], vecs[keep]
for f in gone:
    del state["files"][f]
state["last_run"] = time.time()
json.dump(keys, open("d9/index.json", "w"), ensure_ascii=False)
np.save("d9/vecs.npy", vecs)
json.dump(state, open("d9/state.json", "w"))
print(f"수집 | 문서 {len(files)}개 · 처리 {done} · 지운 문서 {len(gone)} · 실패 {len(failed)} · 새로 임베딩 {embedded} · 색인 {len(keys):,}개 · {time.time() - t:.1f}초")
for f, e in failed:
    print(f"  실패: {f} · {e}")

top = np.argsort(-(vecs @ model.encode("컨피그맵에 저장할 수 있는 데이터 한도는?", normalize_embeddings=True)))[:4]
print(f"확인 | 컨피그맵 한도 → 상위 4청크 중 '1MiB' {sum('1MiB' in keys[i][1] for i in top)}개 · '2MiB' {sum('2MiB' in keys[i][1] for i in top)}개")
