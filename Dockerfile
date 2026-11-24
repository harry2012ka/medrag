# MedRAG container for Railway (or any Docker host).
# - CPU-only PyTorch: the server has no GPU, and the default GPU build adds several GB.
# - The embedding model is downloaded at build time, so the first visitor after a
#   deploy doesn't wait minutes for it.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    MEDRAG_RERANKER=ncbi/MedCPT-Cross-Encoder \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf

WORKDIR /app

COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install -r requirements.txt

# bake the search model into the image
# bake the search model and the answer checker (cross-encoder, about 420 MB RAM) into the image.
# Set MEDRAG_RERANKER=off on the host to run without the checker.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('all-MiniLM-L6-v2'); CrossEncoder('ncbi/MedCPT-Cross-Encoder', max_length=512)"

COPY . .

# run as an unprivileged user
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 8080
CMD ["sh", "-c", "exec streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
