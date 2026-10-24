FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/project

COPY project/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY project/ /app/project/
COPY frontend/ /app/frontend/

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
