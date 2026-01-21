ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY dist /dist
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-client==${PKGVER} --find-links=/dist

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN mkdir -p /root/.ssh
RUN pip install --no-cache-dir /wheels/*.whl
