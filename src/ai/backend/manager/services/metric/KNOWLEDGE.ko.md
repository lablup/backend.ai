# container 자원 사용률 (`services/metric`)

이 도메인은 테이블이 아니라 Prometheus 가 응답하는 시계열을 읽는다. 저장 계층은
`repositories/metric` 이고, 그 아래에는 DB 가 아니라 metric store 가 있다.

## 연산이 지정하는 대상이 모양을 정한다

- metric 이름은 어떤 row 도 지정하지 않으므로 그 읽기는 global 모양이다.
- 시계열은 누구의 container 를 읽는지에 따라 둘로 나뉜다. 호출자 자신의 metric 은 그
  사용자를 지정하므로 single-entity 모양이다. 다른 사용자나 모든 사용자의 metric 을 읽는
  경우는 아무도 지정하지 않으므로 global 로 남는다. 호출부는 대상 사용자와 호출자를
  비교해 둘 중 하나를 고른다.
- live stat 은 호출자가 지정한 커널마다 읽는다. 커널은 엔티티가 아니라 row 이므로 그 읽기는
  bulk-field 모양이다. 그 커널을 소유한 세션을 먼저 읽고 각 세션이 권한을 판정한다.
- 네 연산은 모두 `operation_type() == SEARCH` 를 선언한다. label 이 아무리 좁혀도 필터
  기반 조회다.

## gate 는 연산마다 다르다

- 사용률 panel 은 일반 사용자가 자신의 자원을 보는 곳이므로 superadmin gate 를 두면 기능을
  사용할 수 없게 된다. 대신 호출자 자신의 metric 은 그 사용자에 대한 READ 권한으로
  통과한다.
- metric 이름은 인증만 검사한다. legacy 연결에는 gate 가 아예 없었고, 인증 검사는 public
  으로 옮기면서 들어왔다.
- 다른 사용자의 metric 은 legacy resolver 에 직접 작성한 역할 비교에서 global gate 로
  옮겼다. super admin 은 통과하고, 읽기에서 MONITOR 역할도 통과한다.

## 권한을 판정하는 엔티티는 셋으로 나뉜다

| 연산 | 권한을 판정하는 엔티티 | 이유 |
|---|---|---|
| 사용자 자신의 시계열 | user | label 이 지정한 사용자의 container 를 읽는다 |
| 사용자에 걸친 시계열, metric 이름 | prometheus query preset | 코드에 고정된 질의다. 저장된 preset row 와는 row 가 아니라 내장이라는 점만 다르다 |
| 커널 live stat | session | 커널은 세션의 row 이므로 `LookupBulkKernelOwnerAction` 이 그 세션을 읽고 세션이 권한을 판정한다 |

- 사용자 자신의 metric 은 `Concern.METRIC` 아래 user 그룹의
  `ProcessorGroup.single_entity` 로 연결한다.
- 사용자에 걸친 시계열과 metric 이름은 preset 도메인의 그룹을 함께 사용하며, 각각 global
  gate 와 public gate 뒤에 있다.
- live stat 은 `ProcessorGroup.bulk_field` 로 연결한다.
  `BatchGetKernelResourceAllocationAction` 도 같은 모양을 사용한다.
- processor field 는 `search_user_container_metrics`(자신의 metric), `global_search`(사용자에
  걸친 조회), `metadata_public_search`(metric 이름), `batch_get_kernel_live_stats`(live
  stat) 이다.

## service 는 남는다

- 네 메서드는 모두 외부 시스템(Prometheus)을 호출하므로 generic ops service 로 내려갈 수
  없다. repository spec 을 그대로 전달하는 pass-through 연산이 아니다.
