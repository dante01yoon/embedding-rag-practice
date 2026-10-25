FROM python:3.11-slim
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir sentence-transformers fastapi uvicorn "psycopg[binary]" pgvector redis openai python-dotenv
WORKDIR /app
