---
name: artifact-registry-service-composition
type: decision-table
description: why the HuggingFace and Reservoir registry writes keep service methods, and why their partial bulk runs are service-backed rather than ops-backed
scope: src/ai/backend/manager/services/artifact_registry
keywords:
  - ArtifactRegistryProcessors
  - ArtifactRegistryWriteOps
  - partial_bulk_update_huggingface_registries
  - partial_bulk_purge_reservoir_registries
sources:
  - src/ai/backend/manager/services/artifact_registry/processors.py
  - src/ai/backend/manager/repositories/ops/v2/artifact_registry/write.py
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---

# Artifact registry 서비스

registry 하나는 두 행이다. 연결 설정을 싣는 종류별 행(huggingface, reservoir)과 이름과 종류를 싣는
`artifact_registries` 행. 쓰기는 두 행을 `ArtifactRegistryWriteOps` 의 한 연산으로 같이 쓴다.

## 쓰기가 서비스 메서드를 두는 이유

| 동작 | 모양 | 이유 |
|---|---|---|
| 수정 | `single_entity` + 서비스 | 두 행을 함께 고친다. 일반 ops 수정은 한 행만 쓴다 |
| purge | `single_entity` + 서비스 | 두 행과 그래프 노드를 함께 지운다 |
| 여럿 수정 | `partial_bulk` + 서비스 | 같은 이유. 항목마다 savepoint 하나 |
| 여럿 purge | `partial_bulk` + 서비스 | 같은 이유. 항목마다 savepoint 하나 |

- 여럿 연산은 registry 마다 권한을 따로 본다. 권한이 없는 registry 와 없는 id 는 실패 항목이 되고
  나머지는 처리된다.
- 여럿 purge 의 성공 항목은 지운 registry 의 id 만 싣는다. 이름은 함께 지운 행에 있었다.
- 단건 purge 의 action 은 옛 이름(`delete_*`)을 그대로 쓰고 `PURGE` 연산 종류를 쓴다. 옛 delete 별칭도 같은
  action 을 부른다.
