# Multi-stage Dockerfile for FFBB Data Client API & Web Server
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir ".[server]"

FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0
# Egress proxy par défaut : protège l'IP résidentielle contre toute détection ou blocage WAF BunnyCDN
ENV HTTP_PROXY="http://192.168.1.146:8888"
ENV HTTPS_PROXY="http://192.168.1.146:8888"
ENV NO_PROXY="localhost,127.0.0.1,192.168.1.0/24,dokploy-dnsrr"
ENV REQUIRE_EGRESS_PROXY="1"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "ffbb_data_client.api:app", "--host", "0.0.0.0", "--port", "8000", "--limit-max-requests", "5000", "--limit-max-requests-jitter", "500"]
