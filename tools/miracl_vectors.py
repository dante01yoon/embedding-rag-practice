"""위키 문단 32,651개와 질문 100개를 bge-m3 벡터로 바꿔 vectors/에 저장한다 (A5·A6 수업용, 처음 한 번).
CPU에서는 수십 분 걸릴 수 있다. 문단은 '제목 본문'을 이어 붙여 넣는다 (영상과 같은 방식)."""
import json

import numpy as np
from sentence_transformers import SentenceTransformer

D = "a4/miracl_ko/"
docs = [json.loads(x) for x in open(D + "corpus.jsonl")]
queries = [x.rstrip("\n").split("\t") for x in open(D + "queries.tsv")]
assert [d["docid"] for d in docs] == json.load(open("vectors/docids_ko.json")), "vectors/docids_ko.json과 문단 순서가 달라요"

model = SentenceTransformer("BAAI/bge-m3")
np.save("vectors/queries_ko.npy", model.encode([q for _, q in queries], normalize_embeddings=True))
np.save("vectors/docs_ko.npy", model.encode([d["title"] + " " + d["text"] for d in docs], normalize_embeddings=True, batch_size=32, show_progress_bar=True))
print("저장: vectors/docs_ko.npy · vectors/queries_ko.npy")
