"""오늘 바뀐 문서 (연습용): 컨피그맵 한도 1MiB → 2MiB. DB의 청크를 바꾸고 벡터도 다시 만든다."""
import psycopg
import redis
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

db = psycopg.connect("postgresql://postgres@127.0.0.1:5434/postgres", autocommit=True)
register_vector(db)
model = SentenceTransformer("BAAI/bge-m3")
rows = db.execute("SELECT id, body FROM chunks WHERE body LIKE '%1MiB를 초과할 수 없다%'").fetchall()
for i, body in rows:
    new = body.replace("1MiB를 초과할 수 없다", "2MiB를 초과할 수 없다")
    db.execute("UPDATE chunks SET body = %s, emb = %s WHERE id = %s", (new, model.encode(new, normalize_embeddings=True), i))
ver = redis.Redis(port=6380).incr("index:version")  # 색인이 바뀌었다는 표시
print(f"바뀐 청크 {len(rows)}개 · 색인 버전 {ver}")
