ARG PYTHON_VERSION
ARG PKGVER
FROM python:${PYTHON_VERSION} AS builder
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-client==${PKGVER}

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN mkdir -p /root/.ssh
RUN apt-get update && apt-get install -y vim
RUN pip install --no-cache-dir /wheels/*.whl
