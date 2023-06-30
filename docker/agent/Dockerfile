FROM python:3.9

ARG branch=main

RUN pip install -U -q pip setuptools
RUN apt-get update && \
    apt-get install --no-install-recommends -y netcat libzmq3-dev
RUN mkdir /app
WORKDIR /app
RUN curl https://raw.githubusercontent.com/eficode/wait-for/master/wait-for --output /usr/local/bin/wait-for && \
    chmod +x /usr/local/bin/wait-for
RUN git clone -b $branch --single-branch https://github.com/lablup/backend.ai-agent --depth 50 /app && \
    pip install -U pip setuptools && \
    pip install \
        --no-cache-dir \
        -e "git+https://github.com/lablup/backend.ai-common@$branch#egg=backend.ai-common" \
        -e .

RUN mkdir -p /tmp/vfroot && mkdir -p /tmp/scratches

CMD ["wait-for", "backendai-etcd:2379", "--", "python", "-m", "ai.backend.agent.server"]
