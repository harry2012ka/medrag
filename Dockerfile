# MedRAG container for Railway (or any Docker host).
# - CPU-only PyTorch: the server has no GPU, and the default GPU build adds several GB.
# - The embedding model is downloaded at build time, so the first visitor after a
#   deploy doesn't wait minutes for it.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf

WORKDIR /app

COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install -r requirements.txt

# bake the search model into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

EXPOSE 8080
CMD streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 \
    --server.headless=true --browser.gatherUsageStats=false
