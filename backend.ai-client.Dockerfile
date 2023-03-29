ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-client==${PKGVER}

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN mkdir -p /root/.ssh
RUN apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir /wheels/*.whl
