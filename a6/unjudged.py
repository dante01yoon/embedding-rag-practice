import json

import numpy as np

docs, qv = np.load("vectors/docs_ko.npy"), np.load("vectors/queries_ko.npy")
ids = json.load(open("vectors/docids_ko.json"))
qs = [line.rstrip("\n").split("\t") for line in open("vectors/queries_ko.tsv")]
judged = {}
for line in open("vectors/qrels_ko.tsv"):
    q, d, r = line.split()
    judged.setdefault(q, set()).add(d)  # 정답이든 오답이든 사람이 읽어 본 문서
top = np.argsort(-(qv @ docs.T), axis=1)[:, :10]
unseen = [[ids[j] for j in row if ids[j] not in judged[q]] for (q, _), row in zip(qs, top)]
print("상위 10개 중 판정 안 된 문서:", sum(map(len, unseen)), "/", 10 * len(qs))
for (q, text), u in zip(qs, unseen):
    if len(u) == 10:
        print("10개 모두 판정 없음:", text)
