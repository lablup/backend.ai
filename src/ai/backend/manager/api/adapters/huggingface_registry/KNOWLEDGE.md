---
name: huggingface-registry-adapter-scenarios
type: reference
<<<<<<< HEAD
description: TODO - what the huggingface registry adapter guarantees, as scenarios; nobody has written these yet
scope: src/ai/backend/manager/api/adapters/huggingface_registry
keywords: [huggingface registry, scenario, adapter, todo]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
=======
description: what the huggingface registry adapter guarantees for update, purge and their partial bulk forms, and the token it gives only to a superadmin
scope: src/ai/backend/manager/api/adapters/huggingface_registry
keywords: [huggingface registry, artifact registry, scenario, adapter, rbac, partial bulk, purge, token]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
updated:
  by: claude-code/opus-5
  at: 2026-11-06
>>>>>>> ca95a63b (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))
status: draft
---
# huggingface_registry 어댑터 — 시나리오

TODO. 아직 아무도 적지 않았다.

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 이 파일이 이 모양으로 남아 있는 동안, 이 엔티티는
시나리오 테스트가 없다.

## 적는 법

<<<<<<< HEAD
1. `adapter.py`가 내놓는 호출을 전부 훑는다.
2. 호출마다 무엇을 보장하는지 한 문장으로 적는다. 권한이 있는 경우와 없는 경우를 짝으로 둔다.
3. 동작별로 표를 나눈다. 각 줄은 상황, 요청, 결과 셋을 갖는다.
4. 어느 시나리오도 부르지 않는 호출은 "아직 적지 않은 것"에 남긴다.
=======
## Node

Every node the adapter returns carries the stored `token` only when the caller is a superadmin. Any other caller, a monitor or a user granted update included, gets `*****` in its place. A registry without a token returns null to every caller. The field keeps its type, so the schema does not change.

## Update
>>>>>>> ca95a63b (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))

먼저 적힌 것을 보려면 `../domain/KNOWLEDGE.md`를 참고한다.
