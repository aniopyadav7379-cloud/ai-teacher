FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc tesseract-ocr poppler-utils \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY workers ./workers
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["sh", "-c", "cd backend && alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
