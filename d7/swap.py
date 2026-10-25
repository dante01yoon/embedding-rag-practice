import json
import os
import sys
import time

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
qa = json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json"))  # 골든셋 78개
models = {}


def load(model_id):  # 모델은 한 번만 읽어 둔다
    if model_id not in models:
        models[model_id] = SentenceTransformer(model_id)
    return models[model_id]


def build(name, model_id, passage="", query="", vecs=None):  # 새 색인: 벡터와 함께 어떤 모델로 만들었는지 기록
    os.makedirs(f"d7/idx/{name}", exist_ok=True)
    t = time.time()
    V = vecs if vecs is not None else load(model_id).encode([passage + c for _, c in chunks], normalize_embeddings=True, batch_size=32)
    np.save(f"d7/idx/{name}/vecs.npy", V)
    json.dump({"model": model_id, "dim": V.shape[1], "query_prefix": query}, open(f"d7/idx/{name}/meta.json", "w"))
    print(f"색인 {name:<12} | {V.shape[1]}차원 · {time.time() - t:.1f}초")


def encode(name, texts):  # 그 색인을 만든 모델로 질문을 벡터로
    meta = json.load(open(f"d7/idx/{name}/meta.json"))
    return load(meta["model"]).encode([meta["query_prefix"] + t for t in texts], normalize_embeddings=True)


def hits(name):  # 질문마다 상위 4개 안에 정답 문서가 있나
    top = np.argsort(-(encode(name, [x["question"] for x in qa]) @ np.load(f"d7/idx/{name}/vecs.npy").T), axis=1)[:, :4]
    return np.array([x["path"] in {chunks[j][0] for j in top[i]} for i, x in enumerate(qa)])


def switch(name):  # 별칭 전환: live가 가리키는 색인만 바꾼다 (임시 파일에 쓰고 한 번에 바꿔치기)
    json.dump({"index": name}, open("d7/live.tmp", "w"))
    os.replace("d7/live.tmp", "d7/live.json")


def search(q):  # 서비스: live 색인에서 찾는다
    name = json.load(open("d7/live.json"))["index"]
    i = int(np.argmax(np.load(f"d7/idx/{name}/vecs.npy") @ encode(name, [q])[0]))
    return name, chunks[i][0].split("/")[-1]


build("v1-bge-m3", "BAAI/bge-m3", vecs=np.load("k8s/vecs_ko_500.npy"))  # 지금 쓰는 색인
build("v2-e5-small", "intfloat/multilingual-e5-small", passage="passage: ", query="query: ")  # 모델 설명서대로 앞말을 붙인다
for name in ["v1-bge-m3", "v2-e5-small"]:
    print(f"{name:<12} | Recall@4 {hits(name).mean():.1%}")
switch("v1-bge-m3")
print("live =", search("컨피그맵에 저장할 수 있는 데이터 한도는?"))
switch("v2-e5-small")
print("live =", search("컨피그맵에 저장할 수 있는 데이터 한도는?"))
