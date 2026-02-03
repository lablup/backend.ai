ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY dist /dist
COPY requirements.txt /requirements.txt
# Install dependencies from requirements.txt to respect version constraints
RUN pip wheel --wheel-dir=/wheels --no-cache-dir -r /requirements.txt
# Install backend.ai packages from /dist (these are not in requirements.txt or PyPI)
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-webserver==${PKGVER} --find-links=/dist --no-deps --find-links=/dist

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
COPY dist /dist
# Install all wheels and also look in /dist for backend.ai packages
RUN pip install --no-cache-dir --find-links=/dist /wheels/*.whl

# Create necessary directories
RUN mkdir -p /var/log/backend.ai /etc/backend.ai

# Set working directory
WORKDIR /app

CMD ["python", "-m", "ai.backend.web.server", "-f", "/etc/backend.ai/webserver.conf"]

