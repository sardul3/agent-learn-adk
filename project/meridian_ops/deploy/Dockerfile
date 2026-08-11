FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN useradd -u 10001 -m appuser

COPY project/meridian_ops /app/meridian_ops
COPY project/meridian_orderops /app/meridian_orderops
COPY project/meridian_ops/deploy/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir "google-adk>=2.0.0" mcp

USER 10001:10001
EXPOSE 8080

# Secrets via env at runtime — never bake GOOGLE_API_KEY / MERIDIAN_API_KEY into the image.
CMD ["uvicorn", "meridian_ops.deploy.app:api", "--host", "0.0.0.0", "--port", "8080"]