FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install the SDK + server deps
COPY pyproject.toml README.md wonderwallai/ wonderwallai/
COPY server/ server/
COPY server/requirements.txt server/requirements.txt

RUN pip install --no-cache-dir -e ".[all]" && \
    pip install --no-cache-dir -r server/requirements.txt

# Pre-download the embedding model at build time (avoids cold start)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8080

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8080"]
