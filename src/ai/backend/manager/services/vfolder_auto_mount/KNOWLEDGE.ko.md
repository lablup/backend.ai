# 자동 마운트 vfolder service: 배경

> 규칙은 `../AGENTS.md`, 연결은 `backend.ai mgr ops list` 로 확인한다.

`vfolder_auto_mount` row 는 vfolder 하나를 프로젝트나 사용자의 자동 마운트 vfolder 로 정한다. 세션 시작은 domain repository 를 통해 row 를 조회하고, 이 패키지는 호출자가 API 로 도달하는 operation 을 담는다.

## processor fields

| 필드 | 실패 모드 | 인가 기준 |
|---|---|---|
| `bulk_get_ids` | partial bulk | 지정한 row 각각 |
| `create` | 한 번 실행 | row 를 생성하는 프로젝트나 사용자 |
| `global_search` | 한 번 실행 | 엔티티 종류별 `global` singleton |
| `search` | 한 번 실행 | 지정한 모든 프로젝트, 사용자, vfolder |
| `update` | row 하나 | 지정한 row |
| `delete` | row 하나 | 지정한 row |
| `restore` | row 하나 | 지정한 row |
| `purge` | row 하나 | 지정한 row |

## create 만 service method 를 둔다

- create 의 spec 은 전제 조건(vfolder 가 그 프로젝트나 그 사용자의 것이다)을 담는데 generic create 는 이를 받지 않는다. service 가 이를 domain repository 에 전달한다.
- 다른 operation 은 generic ops service 에 spec 을 전달하므로 `service.py` method 를 갖지 않는다.

## admin search 는 global 이다

- 모든 프로젝트와 모든 사용자의 row 를 조회하므로 검사할 스코프를 지정하지 않는다.

## scoped search 는 스코프별이다

- 호출자는 프로젝트, 사용자, vfolder 를 지정하고, 그중 어느 것의 row 든 조회한다.
- 사용자 스코프는 사용자에 설정한 row 를 조회하고, 개인 프로젝트의 row 는 조회하지 않는다.
- vfolder 스코프는 그 vfolder 를 설정한 모든 프로젝트와 사용자의 row 를 조회한다.

## 두 search 는 기본으로 삭제된 row 를 제외한다

- searcher 는 삭제된 row 까지 조회한다. adapter 가 제외하는 조건을 추가하며, 최상위 필터가 `deleted_at` 을 지정하면 추가하지 않는다.

## id 로 하는 조회는 partial 이다

- GQL DataLoader 에 값을 제공하고, 한 batch 에 여러 resolver 의 id 가 섞인다. 호출자가 조회할 수 없는 row 만 실패한다.
