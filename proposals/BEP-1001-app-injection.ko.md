# App 주입

## 동기

* container app(예: Jupyter)과 container image(예: NGC PyTorch)의 업데이트 주기를 분리한다
* 사용자가 원하는 app version 을 고정할 수 있게 한다(예: Jupyter Notebook v7 은 호환성을 깨는 변경이 많고 대부분의 nbextensions 가 동작하지 않는다)

## 제안 구조

### App 패키지

- `service-def.json` (`/opt/kernel/service-defs/{app-name}.json` 로 마운트)
- `app/` (`/opt/apps/{app-name}/` 로 마운트)

### Manager API 변경

- 사용 가능한 app 패키지를 나열한다
- session 과 kernel 을 생성할 때 필요한 app 패키지를 agent node 에 자동으로 채운다
  (또는 모든 agent node 에 일관된 app 패키지 파일이 있다고 가정해야 한다)
- session 을 생성할 때 app 패키지를 지정한다
- 일부 메타데이터를 비교해 호환성을 검사한다
  (예: 정적 빌드인지, 특정 glibc version 에 의존하는지)

### Agent API 변경

- TODO

## 기존 app 이전

### 전반적인 기술 문제

- 추출한 app 디렉터리를 _읽기 전용_ 으로 마운트하면 일부 app 이 예상대로 동작하지 않을 수 있다.
- app 이 root 만 사용할 수 있는 디렉터리에 의존하면 예상대로 동작하지 않을 수 있다.
- app 패키지를 읽고 추출하는 데 걸리는 지연
- agent 의 disk 크기 한도 안에서 추출한 app 패키지 cache 를 관리하는 일
- PBS(python-build-standalone)를 app 마다 따로 배포하는 방안

### Jupyter

최근 Jupyter 는 설정 형식을 변경했다. (TODO: issue 링크)

포함된 template 문자열에서 설정 파일을 직접 쓰는 대신, service definition 을 변경해 (주입된) script 를 실행하도록 version 별 `.cfg` 파일을 생성해야 한다.

**설계 논의:**
- wheelhouse 디렉터리를 만들고 app 을 처음 실행할 때 설치한다 _vs._ 미리 설치한 site-packages 디렉터리를 만들고 하위 디렉터리를 `/opt/backend.ai` 에 마운트한다
- 처음 실행할 때 최소한 _대상_ Python(container image 에 이미 설치된 Python)에 `ipykernel` 을 설치하고 metakernel spec 을 생성해야 한다([backend.ai-kernels](https://github.com/lablup/backend.ai-kernels/blob/075ca379c7db279f69d4485bf014750af0bb6fdc/python/Dockerfile.3.11-ubuntu22.04#L135-L137) 에서 하는 것과 같다).
  이때 실패하면 명시적으로 에러를 보고해야 한다.

### VSCode

- 정적으로 빌드한 app 패키지를 만드는 방안
- app 패키지가 읽기 전용인 상태에서 사용자가 container 에 자기 extension 을 설치할 수 있게 하는 방안
