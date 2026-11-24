# SSH key service: 배경

> 규칙은 `../AGENTS.md`, spec 선택은 `../../models/specs/KNOWLEDGE.md` 에 있다.

이 패키지는 사용자가 가진 SSH 공개키를 다루고, 세션은 사용자의 default 키를 읽는다.
SSH 키 동작을 user service 와 auth service 에서 떼어 내려고 별도 패키지로 둔다.

## Processor field

`backend.ai mgr ops list --field ssh_keypair` 를 실행하면 연결 목록이 출력된다.

| Field | Backing | 인가 대상 |
|---|---|---|
| `upload` | `SSHKeyService.upload` | action 이 지정한 사용자 |
| `switch_default` | `SSHKeyService.switch_default` | `LookupSSHKeypairOwnerAction` 이 읽은 소유 사용자 |
| `scoped_search` | ops (`atomic_bulk_scoped_search_ops`) | 지정한 사용자 모두 |

## 사용자의 default 는 많아야 하나다

| 동작 | default 에 미치는 효과 |
|---|---|
| `upload` | 사용자에게 default 가 없을 때만 새 키가 default 가 된다 |
| `switch_default` | 이전 default 를 해제하고 지정한 키를 default 로 지정한다 |

- default 를 동시에 변경하는 요청 둘은 `uq_ssh_keypairs_is_default` 에 걸리고, creator 와 default 지정 updater 가 이를 `DefaultSSHKeyConflict` 로 변환한다.

## switch_default 는 소유 사용자에 대한 READ 와 UPDATE 가 필요하다

- `switch_default` 는 키를 지정하므로 processor 가 먼저 소유자 lookup 을 실행하고, 이 lookup 에는 READ 가 필요하다.
- 이어지는 수정은 소유 사용자에 대한 `UPDATE` 이므로 READ 만 받은 호출자는 여기서 거부된다.
- `upload` 는 사용자를 직접 지정하므로 UPDATE 만 필요하다.

## 옛 SSH API 는 아직 user service 와 auth service 에서 실행된다

- REST v1 `/auth/ssh-keypair` 와 admin `*SshKeypairV2` GQL field 는 아직 `UserRepository.replace_default_ssh_key` 와 그 옆 메서드를 호출한다.
- 이 API 들은 purge 뒤 create 로 default 를 교체하고, 사용자를 access key 로 찾는다.
- 이 API 들을 deprecated 처리할 때 이 패키지로 이동한다.
