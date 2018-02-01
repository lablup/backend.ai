FROM python:3.6

ARG branch=1.2

RUN pip install -U -q pip setuptools
RUN apt-get update && \
    apt-get install -y libzmq3-dev libsnappy-dev
RUN mkdir /app
WORKDIR /app
RUN git clone -b $branch --single-branch https://github.com/lablup/backend.ai-agent --depth 50 /app && \
    pip install -e .

RUN mkdir /tmp/vfroot && \
    mkdir -p /tmp/scratches
ENV BACKEND_SCRATCH_ROOT=/tmp/scratches

CMD ["python", "-m", "ai.backend.agent.server"]
