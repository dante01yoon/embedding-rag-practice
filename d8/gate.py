import json
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

S = json.load(open("d8/settings.json"))  # PR에서 바뀌는 설정
docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], S["chunk_size"], S["overlap"])]
vecs = np.load(f"k8s/vecs_ko_{S['chunk_size']}.npy")  # shortcut: 미리 만든 벡터 (크기를 바꾸면 그 크기의 벡터를 먼저 만든다)
qa = json.load(open("k8s/qa_ko_reviewed.json")) + json.load(open("k8s/qa_ko_short.json"))  # 골든셋 78개
model = SentenceTransformer("BAAI/bge-m3")
Q = model.encode([x["question"] for x in qa], normalize_embeddings=True, batch_size=16)
top = np.argsort(-(Q @ vecs.T), axis=1)[:, :S["top_k"]]
recall = np.mean([x["path"] in {chunks[j][0] for j in top[i]} for i, x in enumerate(qa)])

if "--update" in sys.argv:  # 베이스라인은 사람이 확인하고 명령으로만 바꾼다
    json.dump({"recall": recall}, open("d8/baseline.json", "w"))
    print(f"베이스라인 갱신 | Recall@{S['top_k']} {recall:.1%}")
    sys.exit(0)
base = json.load(open("d8/baseline.json"))["recall"]
print(f"골든셋 {len(qa)}개 | Recall@{S['top_k']} {recall:.1%} · 베이스라인 {base:.1%}")
if recall < base - 0.02:  # 2%p 넘게 떨어지면 실패 → CI가 배포를 막는다
    print("실패: 베이스라인보다 낮아요. 배포 중단")
    sys.exit(1)
print("통과")
