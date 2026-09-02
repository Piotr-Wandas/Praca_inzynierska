FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
COPY src /app/src
COPY apps/api /app/apps/api
COPY scripts /app/scripts
COPY sql /app/sql
COPY review /app/review
RUN pip install --no-cache-dir .
CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
