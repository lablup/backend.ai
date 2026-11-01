# 용어집: 상태 묶음

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 쓰지 않는 어휘 | 메모 |
|---|---|---|---|---|
| 활성 상태 | activeness status | deployment 의 활성 여부 상태로 ACTIVE, INACTIVE 값을 가집니다. |   |   |
| 에이전트 상태 | agent status | agent 의 운영 상태로 ALIVE, LOST, RESTARTING, TERMINATED 값을 가집니다. |   |   |
| 아티팩트 리비전 상태 | artifact revision status | artifact revision 의 처리 상태로 SCANNED, PULLING, PULLED, VERIFYING, NEEDS_APPROVAL, AVAILABLE, FAILED, REJECTED 값을 가집니다. |   |   |
| 감사 로그 상태 | audit log status | audit log 기록의 처리 상태로 success, error, unknown, running, denied 값을 가집니다. |   |   |
| 배포 상태 | deployment status | v2 의 deployment 상태로 PENDING, READY, DEPLOYING, SCALING, STOPPING, STOPPED 값을 가집니다. |   |   |
| 엔드포인트 수명 주기 | endpoint lifecycle | 배포 endpoint 의 수명 주기 단계를 나타내는 상태입니다. |   |   |
| 엔드포인트 상태 | endpoint status | endpoint 의 서빙 상태로 READY, PROVISIONING, HEALTHY, UNHEALTHY, DESTROYING, DESTROYED, DEGRADED 값을 가집니다. |   |   |
| 이미지 역할 | image role | 이미지의 용도 구분으로 COMPUTE, INFERENCE, SYSTEM 값을 가집니다. |   |   |
| 이미지 상태 | image status | image 의 상태로 ALIVE, DELETED, PURGING, PURGE_ERROR 값을 가집니다. | ImageStatusType |   |
| 커널 상태 | kernel status | kernel 의 생애 상태로 PENDING, RESERVED, SCHEDULED, PREPARING, BUILDING, PULLING, PREPARED, CREATING, RUNNING, RESTARTING, RESIZING, SUSPENDED, TERMINATING, TERMINATED, ERROR, CANCELLED 값을 가집니다. |   |   |
| 네트워크 유형 | network type | 세션이 쓰는 container 간 network 종류입니다. |   |   |
| 라우트 상태 | route status | deployment 안 route 의 생애 주기 상태입니다. |   |   |
| 서비스 카탈로그 상태 | service catalog status | service catalog 에 등록된 service instance 의 상태 값 묶음입니다. |   |   |
| 세션 상태 | session status | 세션의 생애 상태로 PENDING, PREPARING, RUNNING, TERMINATED 등의 값을 가집니다. |   |   |
| 사용 방식 | usage mode | vfolder 의 용도 값 묶음으로 general, model, data 가 있습니다. |   |   |
| 사용자 상태 | user status | user 계정 상태로 active, inactive, deleted, before-verification 값을 가집니다. |   |   |
| vfolder 작업 상태 | vfolder operation status | vfolder 의 업무 상태와 삭제 단계를 함께 담는 상태 값 묶음입니다. | 폴더 작업 상태 |   |
