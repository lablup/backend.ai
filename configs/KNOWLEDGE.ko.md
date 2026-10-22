# configs/: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다(sample.toml.j2 는 생성되는 template 이므로 직접 수정하지 않는다).

## 이 디렉터리가 있는 이유

컴포넌트마다 설정 스키마 view 와 로컬 개발 template 을 모은다. 이 문서는 설정을 두 출처(파일, etcd)에서 읽는 이유와, key 를 추가할 때 무엇을 갱신하는지에 대한 배경을 담는다.

## 설정 출처는 파일과 etcd 두 가지다

| 출처 | 담는 값 | 변경 전파 |
|---|---|---|
| TOML 파일(컴포넌트별) | node, process 로컬 설정 | boot 때만 읽는다, 재시작이 필요하다 |
| etcd | cluster 전역 설정(공유 자원, volume, redis 연결 등) | 감시한다, 변경 시 전체 설정을 다시 검증한다(hot reload) |

- 두 출처는 하나의 pydantic 통합 설정(`config/unified.py`)으로 병합된다. 코드가 읽는 값은 항상 통합 설정이다.
- key 의 위치 결정: node 마다 다르면 파일, cluster 가 공유하면 etcd.

## 파일은 네 종류이고 하나만 생성된다

| 종류 | 예 | 관리 |
|---|---|---|
| 생성되는 스키마 template | `{component}/sample.toml.j2` | `generate-sample` 로 다시 생성하고, `config render` 로 설정 파일을 만든다 |
| 로컬 개발 template | `halfstack.toml`, `ci.toml`, `halfstack.alembic.ini`, `sample.conf` | 직접 관리한다 |
| etcd seed JSON | `manager/sample.etcd.*.json` | 직접 관리한다 |
| 서드파티 인프라 | prometheus, loki, tempo, grafana, traefik, systemd, graphql | 직접 관리한다 |

- `sample.toml.j2` 를 다시 생성하거나 비교하는 CI 검사는 없다. 차이는 review 에서만 발견된다.
- template 인자를 채우기 전에는 TOML 로 파싱되지 않으므로, 채우지 않은 sample 을 설정으로 쓸 수 없다. `config render` 는 인자가 빠지면 실패하고 결과가 TOML 로 파싱되는지 확인한다. 값은 검증하지 않는다. 검증하면 일부 경로 field 가 가리키는 디렉터리를 만들기 때문이다.

## 읽는 순서

1. TOML 파일
2. 환경 변수 override, **파일보다 우선한다**
3. 명시적 override
4. pydantic 통합 설정으로 검증한다(TOML 은 kebab-case, Python 은 snake_case)

## 설정 key 추가 확인 목록

1. 컴포넌트의 `config/unified.py` 에 `BackendAIConfigMeta` 로 field 를 추가한다. `description` 과 `added_version` 은 필수다(version 은 `# Added in X.Y.Z` 주석이 된다).
2. 다시 생성한다: `./backend.ai {component} config generate-sample --overwrite --unmask-secrets`. 표를 값으로 갖는 DICT field 를 새로 추가하면 `template_arg` 도 지정한다.
3. 로컬 개발에 값이 필요하면 `halfstack.toml`/`ci.toml` 을 직접 갱신한다. 이 파일들은 생성되지 않는다.
4. etcd 기반 key 라면 `unified.py` 의 etcd tree docstring 과 해당 `sample.etcd.*.json` 을 갱신한다.
