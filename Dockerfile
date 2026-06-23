FROM python:3.12-slim

WORKDIR /code

COPY config/requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Pre-download sentence-transformers model at build time so container starts fast.
# Without this the model downloads on first request (~30s cold start).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

CMD ["uvicorn", "autoapply.main:app", "--host", "0.0.0.0", "--port", "8000"]
