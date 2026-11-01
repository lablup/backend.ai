# 컨테이너 레지스트리 서비스: 배경

> 규칙: `../AGENTS.md`. Action shape 와 gate: `../../actions/KNOWLEDGE.md`.

컨테이너 레지스트리는 Manager 가 이미지를 스캔해 오는 global 엔티티다. 이 서비스는 Harbor 가
프로젝트마다 두는 스토리지 quota 도 다룬다. quota 연산은 registry 를 직접 받지 않고,
registry 를 참조하는 프로젝트를 받아 거기서 registry 를 찾는다.

## quota 연산의 권한은 processor 가 아니라 API 단에서 거른다

| 진입점 | gate | 통과하는 역할 |
|---|---|---|
| REST v1 `/group/registry-quota` | route 의 `superadmin_required` middleware | SUPERADMIN |
| 레거시 GraphQL quota mutation | mutation 클래스의 `allowed_roles` | SUPERADMIN, ADMIN |
| 레거시 GraphQL `GroupNode.registry_quota` | 없음 | 노드를 조회할 수 있는 누구나 |

- quota processor 넷은 `anonymous_global` 로 연결된다. monitor 만 붙고 validator 는 없으며,
  카탈로그에는 anonymous gate 로 잡힌다.
- `global` shape 를 사용하지 않은 이유는 그 SUPERADMIN gate 가 레거시 GraphQL mutation 이 허용하는
  ADMIN 을 잘라내기 때문이다.
- 지향점은 프로젝트를 스코프로 삼는 `scope` shape 다. seed role 이 아직 `container_registry: [read]` 만
  주므로, 기록 권한이 role 에 추가된 뒤에 옮긴다.
- webhook processor 도 같은 anonymous 연결이다. Harbor 는 keypair 가 없으므로 서비스가 webhook secret 을
  직접 검사한다.

## quota 연산은 프로젝트를 거쳐 registry 에 접근한다

- `get_project_registry` 는 프로젝트의 `container_registry` 설정에서 registry 이름과 프로젝트명을
  읽고, 그 둘이 참조하는 registry 를 찾는다. 프로젝트, 설정, registry 중 하나라도 없으면
  `ContainerRegistryNotFound` 다.
- 클라이언트 pool 은 registry 타입으로 클라이언트를 고른다. 구현은 `HARBOR2` 뿐이라 다른 타입은
  `ContainerRegistryQuotaNotSupported` 다.
- `project`, `username`, `password` 중 하나라도 null 인 registry 는 Harbor 를 호출하기 전에
  `ContainerRegistryQuotaNotConfigurable` 로 거부된다. `ssl_verify` 는 null 이어도 거부하지 않고
  `True`(TLS 검증)로 본다. column 의 `server_default` 와 같다.
- `HarborQuotaClient` 는 호출마다 세션을 열므로 pool 은 연결 상태를 갖지 않고 close 도 필요 없다.

## 이름과 registry 내부 프로젝트명 조회는 찾은 registry 의 읽기 권한을 검사한다

- `lookup_by_name_and_registry_project` 는 이름과 registry 내부 프로젝트명을 기존 lookup 으로 해석하고 registry ID 를 반환한다.
- 인증 후 lookup 을 수행하고, 찾은 registry 의 읽기 권한을 검사한다. 일반 사용자에게는 미존재와 권한 부족을 같은 오류로 반환한다.
- 여러 registry 가 같은 키에 대응하면 공통 lookup 이 거부하며 임의의 row 를 선택하지 않는다.
