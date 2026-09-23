---
name: container-registry-service-gates
type: decision-table
description: container registries as global entities scanned for images, the per-project Harbor quota operations gated at the API layer instead of the processor, why the quota processors are wired anonymous, how a project resolves to the registry the quota client talks to, the registry conditions that reject a quota operation
scope: src/ai/backend/manager/services/container_registry
keywords: [ContainerRegistryProcessors, ContainerRegistryService, CreateRegistryQuotaAction, ReadRegistryQuotaAction, anonymous_global, superadmin_required, allowed_roles, get_project_registry, ContainerRegistryQuotaClientPool, HarborQuotaClient]
sources:
  - src/ai/backend/manager/services/container_registry
  - src/ai/backend/manager/api/rest/group/registry.py
  - src/ai/backend/manager/api/gql_legacy/container_registry.py
  - src/ai/backend/manager/api/gql_legacy/group.py
  - src/ai/backend/manager/repositories/container_registry/repository.py
  - src/ai/backend/manager/clients/container_registry
generated:
  by: claude-code/opus-5
  at: 2026-09-21
status: stable
---

# 컨테이너 레지스트리 서비스 — 배경

> 규칙: `../AGENTS.md`. 액션 shape와 게이트: `../../actions/KNOWLEDGE.md`.

컨테이너 레지스트리는 매니저가 이미지를 스캔해 오는 전역 엔티티다. 이 서비스는 Harbor가
프로젝트마다 두는 스토리지 quota도 다룬다. quota 연산은 레지스트리를 직접 받지 않고,
레지스트리를 가리키는 프로젝트를 받아 거기서 레지스트리를 찾아간다.

## quota 연산의 권한은 processor가 아니라 API단이 거른다

| 진입점 | 게이트 | 통과하는 역할 |
|---|---|---|
| REST v1 `/group/registry-quota` | route의 `superadmin_required` middleware | SUPERADMIN |
| 레거시 GraphQL quota mutation | mutation 클래스의 `allowed_roles` | SUPERADMIN, ADMIN |
| 레거시 GraphQL `GroupNode.registry_quota` | 없음 | 노드를 조회할 수 있는 누구나 |

- quota processor 넷은 `anonymous_global`로 배선된다. monitor만 붙고 validator는 없으며,
  카탈로그에는 anonymous 게이트로 잡힌다.
- `global` shape를 쓰지 않은 이유는 그 SUPERADMIN 게이트가 레거시 GraphQL mutation이 허용하는
  ADMIN을 잘라내기 때문이다.
- 지향점은 프로젝트를 스코프로 삼는 `scope` shape다. seed role이 아직 `container_registry: [read]`만
  주므로, 쓰기 권한이 role에 추가된 뒤에 옮긴다.
- webhook processor도 같은 anonymous 배선이다. Harbor는 keypair가 없으므로 서비스가 webhook secret을
  직접 검사한다.

## quota 연산은 프로젝트를 거쳐 레지스트리에 닿는다

- `get_project_registry`는 프로젝트의 `container_registry` 설정에서 레지스트리 이름과 프로젝트명을
  읽고, 그 둘이 가리키는 레지스트리를 찾는다. 프로젝트·설정·레지스트리 중 하나라도 없으면
  `ContainerRegistryNotFound`다.
- 클라이언트 pool은 레지스트리 타입으로 클라이언트를 고른다. 구현은 `HARBOR2`뿐이라 다른 타입은
  `ContainerRegistryQuotaNotSupported`다.
- `project`·`username`·`password` 중 하나라도 null인 레지스트리는 Harbor를 부르기 전에
  `ContainerRegistryQuotaNotConfigurable`로 거부된다. `ssl_verify`는 null이어도 거부하지 않고
  `True`(TLS 검증)로 본다. 컬럼의 `server_default`와 같다.
- `HarborQuotaClient`는 호출마다 세션을 열므로 pool은 연결 상태를 갖지 않고 close도 필요 없다.
