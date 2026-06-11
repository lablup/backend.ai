# Manager GraphQL 레이어 — 컨텍스트

> 규칙은 같은 디렉터리 `AGENTS.md`, 구현 패턴은 `/api-guide` 스킬.

## Federation 이름 충돌 caveat

v2 Strawberry 스키마는 v1 Graphene 스키마와 함께 supergraph로 합성된다. `GQL` 접미를 뗀 스키마 이름이
다른 shape의 기존 v1 Graphene 타입(예: `KeyPair`, `CreateContainerRegistryInput`)과 충돌하면 supergraph
합성이 실패한다. 이 경우 `V2` 접미 스키마명을 쓴다(`name="KeyPairV2"`) — 기존 `DomainV2`/`UserV2` 규약과 일치.
이름을 바꾼 뒤 `scripts/generate-graphql-schema.sh`로 합성을 검증한다.

## 페이지네이션 모드 동작

search 쿼리는 커서·오프셋 인자를 모두 받는다.

- **기본(인자 없음):** 오프셋(`limit=10, offset=0`)으로 폴백.
- **오프셋(`limit`/`offset`):** 사용자 지정 `order_by` 적용, 없으면 엔티티 기본 정렬. 커스텀 정렬이 필요할 때.
- **커서(`first`/`after` 또는 `last`/`before`):** 정렬은 엔티티 커서 키(보통 `created_at` 또는 PK)로 고정.
  사용자 지정 `order_by`는 무시한다 — 커서 일관성을 위해 고정 정렬이 필요. 무한 스크롤/"더 보기" UX에 적합.
- 한 요청에 한 모드만. `first`+`limit` 혼용은 에러.
