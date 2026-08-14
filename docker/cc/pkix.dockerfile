FROM python:3.13-slim
RUN pip install --no-cache-dir grpcio==1.71.0 grpcio-tools==1.71.0 cryptography==44.0.2
WORKDIR /opt/pkix
COPY plugin.proto server.py profiles.json ./
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. plugin.proto
ENTRYPOINT ["python", "/opt/pkix/server.py"]
CMD ["--ca-certificate", "/etc/pkix/ca.crt", "--ca-key", "/etc/pkix/ca.key", \
     "--profiles", "/opt/pkix/profiles.json", "--listen", "127.0.0.1:50051", \
     "--tls-certificate", "/etc/pkix/plugin.crt", "--tls-key", "/etc/pkix/plugin.key"]
