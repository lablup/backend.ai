# Backend.AI 컴포넌트 image 빌드 가이드

dood3 (또는 일반 k8s) 배포에 필요한 backend.ai 5 개 컴포넌트 image 를 repo 의 `docker/` 아래 Dockerfile 들로 빌드한 뒤 사설 registry 에 push 하는 절차. 외부에서 pull 만 받으면 되는 보조 image 들도 함께 정리합니다.

> 본 가이드는 `docs/dood3-install.md` 의 §0.1 에서 참조됩니다. 표준 helm install 흐름의 사전 단계.

## 개요

dood3 helm chart 가 가정하는 image 들:

| 컴포넌트 | image (사설 registry 기준) | 빌드 방식 | 빌드 필요? |
|---|---|---|---|
| manager | `<reg>/backend.ai-manager:dev` | 신형 (pants self-build) | ✅ |
| agent | `<reg>/backend.ai-agent:dev` | 신형 | ✅ (LFS 자산 필요) |
| storage-proxy | `<reg>/backend.ai-storage-proxy:dev` | 신형 | ✅ |
| appproxy (coordinator + worker 공용) | `<reg>/backend.ai-appproxy:dev` | 구형 (pre-built wheel) | ✅ |
| webserver | `<reg>/backend.ai-webserver:dev` | 구형 | ✅ |
| apollo-router | `ghcr.io/apollographql/router:v1.55.0` | — | ❌ (외부 pull) |
| postgres / redis / etcd / busybox / python:3.13-slim | 공식 image | — | ❌ |

> `<reg>` = 본 가이드 예시 `192.168.0.156:5000` (ser8 의 사설 registry). 사내 Harbor 등도 동일한 흐름.

### 신형 vs 구형 Dockerfile

두 스타일이 공존하는 이유:
- **신형** (`docker/<component>/Dockerfile`): 컨테이너 안에서 pants 로 wheel 까지 self-build. 호스트에 pants 가 없어도 됨. lab / 1 회성 빌드에 적합. **첫 빌드 10~15 분** (이후 layer cache 로 빨라짐).
- **구형** (`docker/<name>.dockerfile`): 호스트에서 `scripts/build-wheels.sh` 로 미리 `dist/*.whl` 만든 다음 그걸 `COPY dist /dist` 로 들고 들어가 install. CI / release pipeline 에 적합.

결과 image 자체는 두 방식이 같아서, **편한 쪽으로 일관성 있게** 가면 됩니다. 본 가이드는 신형이 있는 컴포넌트는 신형으로, 없는 컴포넌트 (appproxy/webserver) 는 구형으로 빌드.

## 사전 준비 (호스트)

### Docker

```bash
sudo systemctl enable --now docker
docker version    # 확인
```

### Git LFS (agent 빌드 전에 반드시)

agent image 는 `backendai-socket-relay.img.*.tar.gz` / `linuxkit-nsenter.img.*.tar.gz` 등 LFS-tracked 자산을 wheel 에 포함합니다. `git lfs pull` 안 하면 ~132B 의 LFS pointer 파일이 들어가서 agent 가 부팅 시 `gzip.BadGzipFile: Not a gzipped file` 로 죽거나, 더 나쁘게는 통과해서 빈 docker volume 을 kernel container 마다 마운트하는 사일런트 실패가 발생.

```bash
git lfs install              # 사용자 1 회
git lfs pull                 # repo 마다 1 회 + 새 LFS 자산 추가될 때마다
ls -la wheels/krunner/*.tar.gz 2>/dev/null | head -3    # 정상이면 MB 단위 크기
```

### Pants (구형 빌드 시에만)

구형 Dockerfile (appproxy/webserver) 은 호스트에서 wheel 을 빌드한 뒤 끌어옵니다. `./pants` 가 repo root 에 있고 첫 호출 시 자동 install 됨 — 호스트 사전 설치 불필요. 단, 첫 빌드는 의존성 download 로 길어질 수 있음.

### 사설 registry 신뢰 (push 받을 호스트들)

```bash
sudo tee /etc/docker/daemon.json <<'EOF'
{ "insecure-registries": ["192.168.0.156:5000"] }
EOF
sudo systemctl restart docker
```

k8s 클러스터의 모든 worker 노드 + agent 호스트들에 동일하게 적용.

## 컴포넌트별 빌드

모두 **repo root** 에서 실행.

### Manager

`docker/manager/Dockerfile` (신형).

```bash
docker build -f docker/manager/Dockerfile -t backend.ai-manager:dev .
```

- builder stage: `pants package src/ai/backend/{cli,common,logging,plugin,manager}:dist` 로 wheel 빌드
- runtime stage: 새 venv 에 wheel install, `tini -- backend.ai` entrypoint
- entrypoint default: `mgr start-server --config /etc/backend.ai/manager.toml`

### Agent

`docker/agent/Dockerfile` (신형).

```bash
# ❗ git lfs pull 이 완료된 상태여야 함 (위 §사전 준비 참조)
docker build -f docker/agent/Dockerfile -t backend.ai-agent:dev .
```

- builder stage: cli/common/logging/plugin/kernel/accelerator(cuda_open + mock)/agent wheel 빌드
- runtime stage: docker-ce-cli 추가 설치 (DooD pattern — host docker.sock 호출용), iproute2/util-linux/procps 등 진단 도구 포함
- 컨테이너는 root 로 동작 (host docker.sock 권한 + /proc / cgroups 접근)
- entrypoint default: `ag start-server --config /etc/backend.ai/agent.toml`
- dood3 시나리오에선 이 image 를 호스트에 직접 `docker run --net=host` 로 띄움 (`docs/dood3-install.md §4` 참조)

### Storage Proxy

`docker/storage-proxy/Dockerfile` (신형).

```bash
docker build -f docker/storage-proxy/Dockerfile -t backend.ai-storage-proxy:dev .
```

- builder stage: cli/common/logging/plugin/storage wheel 빌드
- 컨테이너는 root 로 동작 (NFS hostPath `/vfroot` 의 owner uid/gid 매핑 단순화 — prod 에선 backendai uid 로 전환 권장)
- entrypoint default: `storage start-server --config /etc/backend.ai/storage-proxy.toml`

### AppProxy (Coordinator + Worker 공용)

`docker/backend.ai-appproxy-coordinator.dockerfile` (구형). coordinator/worker 둘 다 같은 image 를 쓰고, helm chart 의 deployment 가 `command/args` 만 다르게 줘서 분기합니다.

```bash
# 1) wheel 사전 빌드 (※ 한 번 만들어두면 webserver 빌드에도 같이 사용됨)
./scripts/build-wheels.sh

# 2) version 추출
PKGVER=$(./py -c "import packaging.version,pathlib; print(str(packaging.version.Version(pathlib.Path('VERSION').read_text())))")

# 3) image 빌드
docker build -f docker/backend.ai-appproxy-coordinator.dockerfile \
  --build-arg PYTHON_VERSION=3.13-slim \
  --build-arg PKGVER=$PKGVER \
  -t backend.ai-appproxy:dev .
```

- `--build-arg PKGVER=$PKGVER`: `dist/` 의 wheel 파일명에 들어가는 버전 — VERSION 파일 기반
- `worker` 용 별도 Dockerfile (`docker/backend.ai-appproxy-worker.dockerfile`) 도 있지만 결과가 동일하므로 coordinator dockerfile 하나로 양쪽 커버

### Webserver

`docker/backend.ai-webserver.dockerfile` (구형). 위 appproxy 가 이미 wheel 만들었다면 그 dist 재사용.

```bash
# 위 appproxy 단계에서 만든 dist/ 가 그대로 있으면 1, 2 단계 skip 가능
./scripts/build-wheels.sh
PKGVER=$(./py -c "import packaging.version,pathlib; print(str(packaging.version.Version(pathlib.Path('VERSION').read_text())))")

docker build -f docker/backend.ai-webserver.dockerfile \
  --build-arg PYTHON_VERSION=3.13-slim \
  --build-arg PKGVER=$PKGVER \
  -t backend.ai-webserver:dev .
```

## 사설 registry 로 tag + push

```bash
REG=192.168.0.156:5000

for img in \
    backend.ai-manager \
    backend.ai-agent \
    backend.ai-storage-proxy \
    backend.ai-appproxy \
    backend.ai-webserver
do
  docker tag  $img:dev $REG/$img:dev
  docker push $REG/$img:dev
done

# 확인
curl -sf http://$REG/v2/_catalog
```

## 외부 image (빌드 불필요)

helm chart 가 다음을 외부에서 pull. air-gapped 환경이면 사설 registry 로 mirror 후 chart values 의 `image.repository` 항목 조정 필요.

| image | 어디서 쓰임 | tag 예 |
|---|---|---|
| `ghcr.io/apollographql/router` | apollo-router chart | `v1.55.0` |
| `python:3.13-slim` | swarm-network-daemon base (initContainer 에서 `pip install`) | `3.13-slim` |
| `postgres` | manager chart deps StatefulSet | `16` |
| `redis` | manager chart deps StatefulSet | `7` |
| `quay.io/coreos/etcd` | manager chart deps StatefulSet | `v3.5.15` |
| `busybox` | 여러 chart 의 render-config / wait-for-* initContainer | `1.36` |

### Mirror 예 (air-gapped)

```bash
REG=192.168.0.156:5000
for src in \
    ghcr.io/apollographql/router:v1.55.0 \
    python:3.13-slim \
    postgres:16 \
    redis:7 \
    quay.io/coreos/etcd:v3.5.15 \
    busybox:1.36
do
  dst="$REG/$(echo $src | sed 's|.*/||')"
  docker pull "$src"
  docker tag  "$src" "$dst"
  docker push "$dst"
done
```

그 후 각 helm chart 의 values 에서 image.repository 만 `$REG/...` 로 override.

## (옵션) Kernel image mirror

helm install 의 image-rescan Job 이 `cr.backend.ai` (Lablup harbor) 에서 kernel image 카탈로그를 가져옵니다. 인터넷 없으면:

```bash
REG=192.168.0.156:5000

# 필요한 kernel image pull
docker pull cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64

# 사설 registry 로 push
docker tag  cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64 \
            $REG/stable/python:3.13-ubuntu24.04-amd64
docker push $REG/stable/python:3.13-ubuntu24.04-amd64
```

그리고 umbrella chart 의 values 에서 `backend-ai-manager.containerRegistries` 를 사설 registry 가리키도록 override:

```yaml
backend-ai-manager:
  containerRegistries:
    - registryName: my-mirror
      url: http://192.168.0.156:5000
      type: docker
      projects:
        - stable
```

## 검증

빌드 + push 후:

```bash
# registry catalog
curl -sf http://192.168.0.156:5000/v2/_catalog | jq .
# {"repositories":["backend.ai-agent","backend.ai-appproxy","backend.ai-manager","backend.ai-storage-proxy","backend.ai-webserver"]}

# 각 image 의 manifest digest
for img in backend.ai-{manager,agent,storage-proxy,appproxy,webserver}; do
  curl -sf -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
    http://192.168.0.156:5000/v2/$img/manifests/dev | jq -r '.config.digest'
done

# 클러스터 노드에서 pull 테스트
docker pull 192.168.0.156:5000/backend.ai-manager:dev
```

성공하면 `docs/dood3-install.md §1` 의 helm install 진행.

## Troubleshooting

| 증상 | 원인 | 해결 |
|---|---|---|
| agent 부팅 시 `gzip.BadGzipFile: Not a gzipped file` | LFS pull 누락 | `git lfs pull` 후 image 재빌드 |
| `pants: command not found` (구형 빌드) | 호스트에 ./pants 실행 권한 없음 | `chmod +x ./pants` 또는 `./pants --version` 으로 자동 install 트리거 |
| `docker push ... no basic auth credentials` | 사설 registry 가 인증 요구 | `docker login <reg>` 후 재시도 |
| `docker push ... http: server gave HTTP response to HTTPS client` | insecure-registries 설정 누락 | `/etc/docker/daemon.json` 에 `insecure-registries` 추가 + docker 재시작 |
| `pants package` 가 매번 처음부터 다시 빌드 | docker BuildKit cache 미사용 | `DOCKER_BUILDKIT=1 docker build ...` 또는 호스트 `~/.cache/pants` 를 cache mount |
