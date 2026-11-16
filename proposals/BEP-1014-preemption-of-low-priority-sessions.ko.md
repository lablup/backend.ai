# 낮은 우선순위 session 의 선점

## 동기

현재 우선순위 숫자는 0..100 정수 범위이고 기본값은 10 이다.
scheduler 는 우선순위 값이 가장 높은 pending session 부터 배치한다.
자원이 남으면 다음으로 높은 우선순위 값의 pending session 을 배치한다.

우선순위가 높은 pending session 을 최대한 빨리 시작하려고 이미 실행 중인 낮은 우선순위 session 을 선점해야 하는 사용 사례가 있다.

## 명세

### 설정

| Field                  | Scope          | Default     | Description                                                                                                 |
| ---------------------- | -------------- | ----------- | ----------------------------------------------------------------------------------------------------------- |
| `preemptible_priority` | Resource Group | 5           | 우선순위 값이 이 값 이하인 실행 중 session 을 선점 대상으로 만드는 우선순위 임계값이다.                     |
| `preemption_order`     | Resource Group | "oldest"    | 같은 (낮은) 우선순위일 때 실행 중인 session 중 "oldest" 또는 "newest" 를 먼저 선점한다.                      |
| `preemption_mode`      | Resource Group | "terminate" | 선점 방식을 지정한다. 사용 가능한 값은 "terminate", "suspend" 다.                                            |

scheduler 는 resource group scope 에서 실행되므로 이 설정은 resource group 별로 둔다.

`preemption_mode == "terminate"` 를 먼저 구현한다.
`"suspend"` 는 아래 논의를 참조한다.

### 구현

scheduler 는 다음과 같이 선점 필요 여부를 판단한다:

- job queue 맨 앞의 pending session 을 배치할 자원이 충분하지 않다.
- job queue 맨 앞의 pending session 보다 우선순위가 낮은 실행 중 session 이 있다.

선점할 때 우선순위가 같거나 다른 실행 중 session 이 여럿일 수 있다.
pending session 을 시작할 만큼 자원이 확보될 때까지 다음 순서로 선점할 session 을 고른다:

* 가장 낮은 우선순위 값
* job 시작 시각
  - `preemption_order` 설정에 따라 오래된 것 먼저 또는 최신 것 먼저

### frontend 와 UI

* WebUI 는 resource policy 가 허용하면 session 을 생성할 때 우선순위 값을 설정할 수 있어야 한다.

### resource policy

* project 별 resource policy 와 user resource policy 는 다음을 정할 수 있어야 한다:
  - 기본 우선순위
  - 우선순위 변경 가능 여부 활성/비활성
  - 활성일 때 설정할 수 있는 우선순위 값 범위


## 논의

### Slurm 과의 유사점과 차이점

Slurm 에는 이 BEP 에서 설명한 선점 로직처럼 동작하는 [preemption](https://slurm.schedmd.com/preempt.html) 개념이 있다.

Slurm 은 개별 job 마다 우선순위 값을 두는 대신 partition 개념을 두고 `PriorityTier` 와 `PreemptMode` 설정을 partition 에 매핑해 job 을 partition 에 추가한다.
job 이 "preemptible" partition 안에 생성되면 자원 경쟁이 있을 때 scheduler 가 그 job 을 종료할 수 있다.

Backend.AI 에서 _resource group_ 은 Slurm 의 partition 과 비슷하지만 물리 또는 논리 node 의 중복되지 않는 집합이다.
물리 node 하나를 compute resource 가 서로 중복되지 않는 여러 논리 node 로 나눌 수 있다.

pending session 의 우선순위 값을 설정하고 `preemptible_priority` 를 조정해 preemptible partition 을 모사할 수 있다.

### 선점된 session 의 중단과 재개

> [!WARNING]
> 이 절은 논의가 필요하다.

`preemption_mode == "suspend"` 이면 session 상태와 메타데이터를 저장했다가 나중에 재개해야 할 수 있다.

주요 사용 사례는 다음과 같다:

* 선점된 session 이 내부에 checkpoint 와 재개 기능을 가진 batch job 이다.

다만 다음 경우에는 해당하지 않을 수 있다:

* 선점된 session 이 inference job 이다
  - autoscaling 기능이 자원이 확보되면 replica 를 자동으로 복원한다.
  - 이 자동 복원도 inference deployment 의 우선순위를 따른다.
* 선점된 session 이 작업 재개에 사람의 개입이 필요한 interactive job 이다.

중단된 session 을 재개하려면 종료할 때 설정과 메타데이터를 보관하고, 자원이 확보되면 다시 pending session 으로 만들어야 한다.
조건과 달성 방법을 정의해야 한다.

**가능한 접근:**

* container 를 종료하되 session object 를 "suspended" 로 표시해 유지한다.
  재개할 때 session 을 다시 enqueue 하고 scheduler 가 같은 설정으로 새 session 을 생성하게 한다.
* container 를 중지하고 session 을 "suspended" 로 표시하되 제거하지 않는다.
  재개하거나 다시 시작한 container 가 로컬 자원(예: scratch 디렉터리)을 재사용할 수 있다.
