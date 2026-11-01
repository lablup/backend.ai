# Artifact registry 서비스: 배경

registry 하나는 두 row 다. 연결 설정을 담는 종류별 row(huggingface, reservoir)와 이름과 종류를 담는
`artifact_registries` row. 기록은 두 row 를 `ArtifactRegistryWriteOps` 의 한 연산으로 함께 처리한다.

## 기록이 서비스 메서드를 두는 이유

| 동작 | shape | 이유 |
|---|---|---|
| 수정 | `single_entity` + 서비스 | 두 row 를 함께 수정한다. 일반 ops 수정은 한 row 만 기록한다 |
| purge | `single_entity` + 서비스 | 두 row 와 그래프 노드를 함께 삭제한다 |
| 여럿 수정 | `partial_bulk` + 서비스 | 같은 이유. 항목마다 savepoint 하나 |
| 여럿 purge | `partial_bulk` + 서비스 | 같은 이유. 항목마다 savepoint 하나 |

- 여럿 연산은 registry 마다 권한을 따로 검사한다. 권한이 없는 registry 와 없는 id 는 실패 항목이 되고
  나머지는 처리된다.
- 여럿 purge 의 성공 항목은 삭제한 registry 의 id 만 담는다. 이름은 함께 삭제한 row 에 있었다.
- 단건 purge 의 action 은 옛 이름(`delete_*`)을 그대로 사용하고 `PURGE` 연산 종류를 사용한다. 옛 delete 별칭도 같은
  action 을 호출한다.
