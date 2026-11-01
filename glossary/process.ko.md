# 용어집: 절차, 문서

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 사용하지 않는 어휘 | 메모 |
|---|---|---|---|---|
| additive only | additive only | field 이름과 용도를 바꾸지 않고 새 field 추가와 기존 field deprecate 만 하는 v2 schema 정책입니다. |   |   |
| 에이전트 heartbeat | agent heartbeat | agent 가 가용 상태를 manager 에 주기적으로 알리는 신호입니다. | heartbeat |   |
| AGENTS.md | AGENTS.md | AI 코딩 에이전트용 규칙만 담는 문서입니다. |   |   |
| 백필 | backfill | 기존 데이터를 새 기능이 쓸 수 있게 미리 채워 넣는 일입니다. |   |   |
| background task | background task | 비동기로 처리하며 task id 를 발급하고 완료를 event 로 알리는 장시간 작업입니다. | bgtask |   |
| 백포트 | backport | main 에 merge 된 변경을 release branch 로 옮기는 과정입니다. |   |   |
| 블루그린 배포 | blue-green deployment | 기존 배포를 Blue 로 두고 새 배포로 트래픽을 전환하는 배포 방식입니다. |   |   |
| 변경 기록 항목 | changelog fragment | changes/ 아래에 두고 towncrier 로 릴리스 노트에 포함하는 PR 단위 요약 파일입니다. | news fragment, 뉴스 프래그먼트, 변경 기록 조각 |   |
| CSV로 내보내기 | CSV export | domain 별로 field 와 filter 를 지정해 CSV 로 내려받는 동작입니다. | CSV 내보내기 |   |
| 위임 | delegation | 다른 Reservoir 로 scan 이나 import 요청을 넘겨 cross 작업을 대신 수행하게 하는 기능입니다. | Delegate Import, Delegate Scan |   |
| 헬스 체크 | health check | model service 의 정상 여부를 확인하는 검사입니다. |   |   |
| KNOWLEDGE.md | KNOWLEDGE.md | 배경 지식과 결정 근거를 담는 문서입니다. |   |   |
| 지원 중인 버전 | maintained version | `.github/maintained-versions.yml` 에 등재되어 fix PR 이 자동 backport 되는 release version 입니다. |   |   |
| 메이저 업그레이드 | major upgrade | 기능 추가와 구조 변경을 포함하는 cluster 업그레이드입니다. |   |   |
| 마이너 업그레이드 | minor upgrade | major version 을 유지하면서 올리는 cluster 업그레이드입니다. |   |   |
| 모노 레포 | monorepo | backend 스택을 한 저장소에 담는 개발 저장소 구성입니다. | mono-repo, mono-repository, semi-mono repository |   |
| 선점 | preemption | 자원이 부족할 때 낮은 우선순위의 실행 중 session 을 밀어내 다른 session 을 배치하는 기능입니다. |   |   |
| 릴리스 브랜치 | release branch | major release 마다 6개월 주기로 만드는 x.y 형태의 branch 이름입니다. |   |   |
| 릴리스 태그 | release tag | patch release 마다 만드는 x.y.z 형태의 tag 이름입니다. |   |   |
| 보존 정책 | retention policy | retention 기간이 지난 기록을 purge 하는 규칙으로 카테고리마다 하나입니다. |   |   |
| 리비전 병합 체인 | revision merge chain | 요청이 비워 둔 model definition 필드를 낮은 우선순위부터 model_mount_destination 기본값, runtime variant baseline, revision preset, deployment-config.yaml, model-definition.yaml, override 순으로 채우는 병합 체인입니다. | merge chain |   |
| 시나리오 | scenario | 어댑터 하나를 실제 database 와 Valkey 로 돌려 요청 하나가 무엇을 답하는지 확인하는 테스트 단위입니다. |   |   |
| 스케줄링 이력 | scheduling history | session 의 scheduling 시도마다 phase 와 상태 변화, 결과, 시도 횟수를 남기는 기록입니다. |   |   |
| seed | seed | mgr seed 명령이 seeds/ 아래 YAML 로 초기 row 를 채우는 기능입니다. |   |   |
| 서비스 카탈로그 heartbeat | service catalog heartbeat | service catalog entry 가 살아 있음을 갱신하는 신호입니다. | heartbeat |   |
| 서비스 디스커버리 | service discovery | agent 가 etcd 로 cluster 에 등록하고 service instance 등록을 event 로 알리는 기능입니다. | SD, 서비스 복구 |   |
| 스킬 | skill | Claude Code 가 개발 작업에 호출하는 안내 문서입니다. |   |   |
| 스윕 | sweep | retention policy 가 자기 category 를 정리하는 동작입니다. | swept |   |
| 사용량 버킷 | usage bucket | 한 scope 가 한 resource group 에서 한 기간 동안 사용한 자원 사용량 기록입니다. |   |   |
