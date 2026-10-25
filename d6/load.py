import json
import sys

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402

docs = json.load(open("k8s/docs_ko.json"))
chunks = [(d["path"], c) for d in docs for c in split(d["text"], 500, 100)]
vecs = np.load("k8s/vecs_ko_500.npy")
db = psycopg.connect("postgresql://postgres@127.0.0.1:5434/postgres", autocommit=True)
db.execute("CREATE EXTENSION IF NOT EXISTS vector")
register_vector(db)
db.execute("DROP TABLE IF EXISTS chunks")
db.execute("CREATE TABLE chunks (id int PRIMARY KEY, path text, body text, emb vector(1024))")
with db.cursor().copy("COPY chunks (id, path, body, emb) FROM STDIN WITH (FORMAT BINARY)") as cp:
    cp.set_types(["int4", "text", "text", "vector"])
    for i, ((p, c), v) in enumerate(zip(chunks, vecs)):
        cp.write_row((i, p, c, v))
db.execute("CREATE INDEX ON chunks USING hnsw (emb vector_cosine_ops)")
print(f"적재 | 청크 {db.execute('SELECT count(*) FROM chunks').fetchone()[0]:,}개 · HNSW 색인")
