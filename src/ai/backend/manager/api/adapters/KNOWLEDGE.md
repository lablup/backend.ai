---
name: adapter-auth-and-scope
type: design-rationale
description: adapters as the single place for auth context and scope building, my search built on scoped_search by handlers and resolvers, and why response nodes carry entity_id/field_id beside the Relay id
scope: src/ai/backend/manager/api/adapters
keywords: [adapter, my_, current_user, OperationScope, self-service, entity_id, field_id, Relay id]
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager API adapters — Knowledge

> For rules, see the API layer `AGENTS.md`; for implementation patterns, see the `/api-guide` skill.

## Adapters own auth context and scope building

An adapter is the single implementation behind both API surfaces (REST v2 and GraphQL).
It builds the `OperationScope`, carries the caller context, and maps DTOs — handlers and
resolvers only pass the parsed input through. `my` searches are the exception: the handler and resolver build the user scope.

## The `my_` pattern

For an entity with a scoped search, the `my` search has no adapter method of its own. The REST handler takes the user
from `UserContext` and the GQL resolver from `current_user()`; each builds the user scope and calls `scoped_search`. The
scope permission check runs on the same path as the scoped search. This keeps each entity from gaining another adapter method.

A `my_` operation with no matching scoped search still takes the user context from `current_user()` inside the adapter
and builds the `OperationScope` there.

## 연산 이름을 하나로 맞추는 이유

같은 동작이 adapter, processor, service에서 다른 이름이면 호출 경로를 따라갈 때마다 대응표가
필요하다. 이름이 같으면 한 번의 검색으로 세 층이 모두 나온다.

`admin_`은 게이트를 이름에 적은 것이다. 게이트는 Action의 모양(전역, 스코프, 단일 엔티티)이
이미 말하므로 이름에 다시 적으면 둘이 어긋날 수 있다. `node`는 GQL 타입 이름이 아래 층으로
스며든 것이다.

REST 경로와 핸들러 이름, GQL 필드 이름은 공개 계약이라 이 규칙과 무관하게 그대로 둔다. REST
핸들러 이름은 OpenAPI의 operationId가 된다.

## 다른 엔티티의 processor를 받지 않는 이유

도메인 adapter가 리소스 그룹 processor로 리소스 그룹 이름을 풀던 때, 두 엔티티의 adapter가
서로의 processor를 들고 있었다. GQL resolver가 리소스 그룹 adapter의 `lookup_name`을 먼저 부르고 id를
넘기면 도메인 adapter는 자기 processor 하나만 받는다. 이름 해석의 권한 판단도 한 곳에 남는다.
`lookup_name`은 인증만 보고, 권한은 id를 받은 연산이 본다.

REST handler와 GQL resolver가 만들어 adapter에 넘기던 `UserInfo`는 Action이 쓰지 않았다.
validator가 요청 문맥의 `current_user()`로 권한을 판단하므로 같은 정보가 두 곳에 있었다.

도메인이 이 규칙을 처음 따랐다. 다른 엔티티는 같은 에픽의 후속 작업이 옮긴다.

## Why `entity_id` / `field_id` sit beside `id`

The GQL `id` is a Relay global id: the type name and the row key base64-encoded into one
opaque value that clients do not look inside. The REST v2 `id` exposes that inner key as
is, and what the key is differs per entity: domains and resource groups use a name,
keypairs an access key, agents a string id. Recovering the row's UUID from `id` therefore
works differently per entity, and not at all where a name is the key.

`entity_id` and `field_id` expose that UUID under one name. The adapter takes the value
from the data class, so it does not depend on what `id` holds. They are present even
where the inner key of `id` is already the UUID: the two values then match, but `id` is
what Relay reads and `entity_id` is what a client passes to other APIs.

Entities and fields are named apart for the same reason `data/` splits them: an entity
row carries its own membership and a field row does not. The name tells from the response
alone whether a permission can be asked on that row.

Fair share values and resource allocation rows are outside the rule. The former are
computed per (resource group, scope) pair and the latter per (kernel, slot name); neither
is stored under a row id.
