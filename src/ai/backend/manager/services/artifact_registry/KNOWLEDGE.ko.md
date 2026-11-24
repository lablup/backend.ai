# Artifact registry 서비스: 배경

registry 하나는 두 row 다. 연결 설정을 담는 종류별 row(huggingface, reservoir)와 이름과 종류를 담는
`artifact_registries` row. 쓰기는 두 row 를 `ArtifactRegistryWriteOps` 의 한 연산으로 함께 처리한다.

## 쓰기가 서비스 메서드를 두는 이유

| 동작 | shape | 이유 |
|---|---|---|
| 수정 | `single_entity` + 서비스 | 두 row 를 함께 수정한다. 일반 ops 수정은 한 row 만 사용한다 |
| purge | `single_entity` + 서비스 | 두 row 와 그래프 노드를 함께 삭제한다 |
| 여럿 수정 | `partial_bulk` + 서비스 | 같은 이유. 항목마다 savepoint 하나 |
| 여럿 purge | `partial_bulk` + 서비스 | 같은 이유. 항목마다 savepoint 하나 |

- 여럿 연산은 registry 마다 권한을 따로 검사한다. 권한이 없는 registry 와 존재하지 않는 id 는 실패 항목이 되고
  나머지는 처리된다.
- 여럿 purge 의 성공 항목은 삭제한 registry 의 id 만 담는다. 이름은 함께 삭제한 row 에 있었다.
- 단건 purge 의 action 은 옛 이름(`delete_*`)을 그대로 사용하고 `PURGE` 연산 종류를 사용한다. 옛 delete 별칭도 같은
  action 을 호출한다.

## 결과의 자격 증명

registry 를 담는 결과는 호출자가 superadmin 일 때만 저장된 Reservoir `secret_key` 와 HuggingFace `token` 을
담는다. 그 밖의 호출자는 `*****` 를 받고, token 이 없는 HuggingFace registry 는 null 을 그대로 받는다.

| 동작 | shape | 이유 |
|---|---|---|
| 여럿 조회 | `partial_bulk` + service | 결과를 호출자에 맞춰 마스킹한다. 일반 ops 조회는 조회 뒤에 다른 단계를 두지 않는다 |

- artifact 가져오기는 이 action 을 거치지 않고 `ReservoirRegistryRepository` 와 `HuggingFaceRepository` 에서
  자격 증명을 직접 읽으므로 저장된 값을 받는다.

