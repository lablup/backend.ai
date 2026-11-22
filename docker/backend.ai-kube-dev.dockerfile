# Development image for the in-cluster components (session controller, ...): the working
# tree's src/ on top of requirements.txt. Build context MUST be the repository root:
#   docker build -f docker/backend.ai-kube-dev.dockerfile -t <ref> .
# Released images use the shared backend.ai-base image instead.
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
COPY ./VERSION /app/VERSION
COPY ./src/ai/backend /app/src/ai/backend
RUN find /app/src -name __pycache__ -prune -exec rm -rf {} +
WORKDIR /app
USER 65534:65534
ENTRYPOINT ["python", "-m"]
