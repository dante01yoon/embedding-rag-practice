# pgvector가 들어 있는 PostgreSQL을 Docker로 띄운다 (내 컴퓨터에서만 접속, 비밀번호 없이)
docker run -d --name rag-pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:5433:5432 pgvector/pgvector:pg17
until docker exec rag-pg pg_isready -q; do sleep 1; done  # DB가 준비될 때까지 기다린다
echo "DB 준비 완료"
