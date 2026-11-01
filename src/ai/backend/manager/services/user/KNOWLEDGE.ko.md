# User service: 배경

사용자는 도메인 아래에 있으므로 생성은 도메인을 스코프로 하는 scope shape 이고, 기존 사용자를 지목하는 operation 은 single-entity 다. keypair 는 사용자의 field row 이므로 keypair 에 대한 모든 operation 은 own 하는 사용자가 처리한다.

## keypair operation 의 shape

keypair row 는 자체 소속을 갖지 않는다. access key 로 keypair 를 지목하는 요청은 key owner lookup 으로 own 하는 사용자를 먼저 조회하고, 이어지는 operation 이 그 사용자를 지목한다. 모든 쓰기는 UPDATE 다. keypair row 를 추가하거나 제거하는 일은 그 사용자에 대한 변경이다.

## Bootstrap script 와 dotfile

- `bootstrap_scripts` 는 `(entity_type, entity_id)` 마다 script 를 담는다. `user_default_bootstrap_scripts` 는 사용자의 기본 script 를 참조하고, 사용자당 0개 또는 1개다.
- script 내용은 `bootstrap_script_revisions` 에 있고, 이 테이블은 row 만 추가한다. update 는 요청한 사용자를 `creator_id` 로 하여 다음 `revision_number` 를 추가하고, 최신 revision 이 현재 내용이다.
- legacy API 와 세션 생성은 사용자의 살아 있는 기본 script 의 최신 revision 을 사용한다. 기본 script 가 없으면 조회는 빈 script 를 반환하고 legacy update 는 script 를 생성해 기본으로 지정한다.
- v2 세션 생성은 script 가 없는 요청을 사용자의 기본 script 로 채우고, 그다음 자원 그룹의 기본 execution spec 으로 채운다.
- `processors.bootstrap_script` 에서 script 를 id 로 지목하는 operation 인 get, bulk get, add revision, purge 는 dangling lookup field 그룹에 있다. owner lookup 이 row 의 `entity_type` 으로 소유자를 찾고, 그 소유자가 operation 을 처리한다. 소유자를 이름으로 받는 operation 은 사용자 single-entity action 인 create, switch default, unset default 와 사용자 scope search 다. 삭제된 script 도 살아 있는 것과 같이 조회하고 purge 한다. switch-default 와 add-revision 은 삭제된 script 에 대해 찾을 수 없음으로 응답한다.

| Operation | 규칙 | 이유 |
|---|---|---|
| create | 항상 non-default 이고 같은 트랜잭션에서 revision 1 을 생성한다 | 기본은 switch-default 로만 옮긴다 |
| add-revision | 기본 여부와 관계없이 살아 있는 script 에 다음 revision 을 추가한다. creator 의 전제 조건이 삭제된 script 를 거부한다 | revision 은 row 만 추가한다 |
| switch-default | 사용자의 지정 row 를 그 사용자에 설정된 살아 있는 script 로 upsert 한다 | 사용자당 지정 row 는 하나다 |
| purge | 기본으로 지정된 script 는 거부한다. 그 revision 은 cascade 로 함께 삭제된다 | 기본 keypair 와 같다. 기본을 먼저 전환한다 |
| unset default | 지정 row 를 삭제하고 script 는 남긴다 | 사용자에게 기본 script 가 없을 수 있다 |

- `dotfiles` 는 row 마다 파일 하나를 `entity_type`, `entity_id`, `path`, `perm`, `data`, `is_default` 와 함께 저장한다. 엔티티마다 path 당 기본 row 는 최대 하나다. 사용자 API 와 세션이 이 row 를 사용한다.
- `(entity_type, entity_id)` 는 `ON DELETE CASCADE` 로 `virtual_entities` 를 참조한다. node 가 없는 엔티티에 생성하면 실패하고, 소유자가 purge 되는 동안 생성한 row 는 node 와 함께 삭제된다.
- 프로젝트와 도메인의 dotfile 은 기존 column 에 남는다.
- 생성은 non-default 파일을 저장한다. 그 ActionResult 는 `entries` 를 유지한다. 기존 기본 파일 뒤에 새 파일이 온다. 현재 기본 파일을 선택하는 runtime operation 은 없다. 마이그레이션된 기본 파일은 계속 사용할 수 있다.
- 요청은 파일마다 `data` 를 `MAXIMUM_DOTFILE_SIZE` 문자로 제한한다. row 의 CHECK 가 강제하는 한도다.
- adapter 가 `DotfileEntryCreator` 를 생성한다. `CreateDotfileAction` 이 이를 `UserRepository` 에 전달하고, repository 가 한 트랜잭션에서 write ops 를 호출한다. `DotfileEntryCreator` 가 소유자를 지목하고 `CreateDotfileAction` 이 거기서 사용자를 받는다.
- 마이그레이션은 keypair 의 byte 를 풀고, 사용자마다 `(path, perm, data)` 의 중복을 제거하며, 원본 중 기본 keypair 가 있었는지를 유지한다. row 를 batch 로 읽고 insert 마다 최대 1,000개 파일 row 를 쓴 뒤 `keypairs.dotfiles` 를 삭제한다.
- downgrade 는 사용자마다 기본 파일을 msgpack 으로 묶어 그 사용자의 모든 keypair 에 복원한다.
- 조회는 `DotfileProcessors` 의 `SearchDotfilesAction` 이고 사용자를 스코프로 하는 scope shape 이며, 소유자의 종류가 row 의 값이므로 dangling field 그룹에 있다. legacy 단일 파일 조회는 path 조건을 추가한 그 search 다. `UpdateDotfileAction` 과 `PurgeDotfileAction` 은 id 로 row 하나를 지목하고, 그 lookup 이 읽은 소유자가 operation 을 처리한다. legacy update 와 delete 는 path 로 기본 row 의 id 를 먼저 찾는다.
- 기존 dotfile API 에서는 access key 로 own 하는 사용자를 선택한다. 사용자를 purge 하면 그 dotfile row 도 삭제된다.

## service 를 두는 operation

생성, purge, bulk operation 묶음, 모든 keypair operation, 월별 통계, dotfile 쓰기 묶음은 service 에 남는다. 생성은 keypair 를 사용자와 함께 생성하고, purge 는 vfolder 와 세션, endpoint 를 정리한다. global, 도메인별, 프로젝트별, 역할별 네 가지 조회는 ops 로 바로 간다.

## 역할은 사용자가 속한 스코프가 아니다

`search_users_by_role` 은 조건을 가진 global search 이지 scope search 가 아니다.
