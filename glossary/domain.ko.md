# 용어집: 제품, 도메인 개념

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 쓰지 않는 어휘 | 메모 |
|---|---|---|---|---|
| 가속기 | accelerator | agent 에 설치해 resource slot 을 추가하는 플러그인입니다. | Compute Plugins, 액셀러레이터 |   |
| 에이전트 | Agent | 노드에서 컨테이너 라이프사이클을 관리하고 자원 사용을 감시하며 Manager 에 상태를 보고하는 컴포넌트입니다. | 실행 노드, compute node, 컴퓨트 노드 | Backend.AI 문서 안에서는 Agent 만 써도 됩니다. 에이전트를 가리키지 않고 실행되는 노드만 말할 때는 node 로 씁니다 |
| 에이전트 선택 전략 | agent selection strategy | 세션을 배치할 agent 를 고르는 전략입니다. |   |   |
| 알림 | alert | 모니터링 지표 임계값에 따라 외부 메시징 서비스로 자동 알림을 보내는 기능입니다. |   |   |
| 별칭 | alias | 마운트할 때 폴더 이름 대신 쓰는 경로입니다. | 대체 이름, 대체이름 |   |
| 엔드포인트 | API endpoint | 접속할 API 서버 주소입니다. | 엔트포인트 |   |
| 앱 설정 | app config | 보이는 모든 scope 의 fragment 를 병합한 app config key 의 값입니다. | AppConfig |   |
| 앱 설정 허용 목록 | app config allow list | config 이름별로 scope 가 값을 쓸 수 있는지와 fragment 병합 순위를 정하는 목록입니다. |   |   |
| 앱 서비스 | app service | 세션 안에서 시작하는 application service 입니다. | 세션 앱 서비스 |   |
| 아티팩트 | artifact | 아티팩트 레지스트리에 있는 모델, 패키지, 이미지입니다. |   |   |
| 아티팩트 레지스트리 | artifact registry | HuggingFace Hub, Reservoir 같은 외부 소스의 AI 모델, 패키지, 이미지를 관리합니다. |   |   |
| 아티팩트 리비전 | artifact revision | registry scan 으로 만들어지고 따로 import 되는 artifact 의 버전입니다. |   |   |
| 아티팩트 저장소 | artifact storage | 시스템 설정에 미리 구성된 아티팩트 저장 목적지입니다. |   |   |
| 아티팩트 유형 | artifact type | artifact 의 종류 묶음입니다. |   |   |
| 감사 로그 | audit log | 누가 어떤 action 을 무엇에 실행했는지 남긴 기록입니다. |   |   |
| 자동 마운트 vfolder | auto-mount vfolder | project 나 사용자가 만드는 모든 session 에 자동으로 마운트되는 vfolder 입니다. | Auto-mount vfolders, 자동 마운트, vfolder auto-mount, 자동 마운트 폴더 |   |
| 오토스케일링 규칙 | auto-scaling rule | 지표에 따라 deployment 의 replica 수를 조정하는 규칙입니다. |   |   |
| Backend.AI | Backend.AI | 컨테이너 기반 컴퓨팅 클러스터 플랫폼입니다. |   |   |
| 기본 이미지 | base image | container 나 VM 기반 kernel 에 붙는 이미지입니다. |   |   |
| 부트스트랩 스크립트 | bootstrap script | session 이 시작할 때 실행하는 스크립트입니다. |   |   |
| 알림 채널 유형 | channel type | 알림 채널의 종류 구분입니다. |   |   |
| circuit | circuit | client 에서 session service 로 가는 라우팅 규칙입니다. |   | 앞으로 manager 관리로 옮기며 ingress 로 대체합니다 |
| 클라이언트 IP 마스킹 | client IP masking | target_type 하나당 하나의 정책 행으로 client IP 를 마스킹합니다. |   |   |
| 클러스터 모드 | cluster mode | session 이 단일 node 인지 여러 node 인지 나타내는 값입니다. |   |   |
| 코드 실행 | code execution | interactive 세션과 상호작용하는 API 입니다. |   |   |
| 실행 환경 | compute environment | container registry 에서 스캔해 화면에 표시하는 image 환경 목록입니다. | 계산 환경, 계산환경 |   |
| 세션 배치 계산 | compute schedule | 프로비저닝 없이 세션이 resource group 에 배치 가능한지 계산하는 동작입니다. |   |   |
| 컨테이너 레지스트리 | container registry | container image 를 받아 오는 registry 와 접근 자격 증명입니다. | 레지스트리 |   |
| 컨트롤 패널 | Control Panel | manager 용 고급 관리·감시 add-on 서비스입니다. |   |   |
| 커스텀 이미지 | custom image | session commit 으로 만들어진 image 입니다. | customized image, 사용자 정의 이미지 |   |
| 대시보드 | dashboard | 실시간과 과거 성능 지표를 보여주는 add-on 서비스입니다. | Backend.AI Dashboard |   |
| 배포 | deployment | 유지할 replica 수와 그것을 서비스하는 replica group 을 가진 model service 입니다. | Model Service, 모델 배포 |   |
| 배포 에이전트 지정 | deployment agent designation | 배포를 배치할 agent 를 지정하는 기능입니다. | deployment designated agent, 배포 지정 에이전트 |   |
| 배포 엔드포인트 | deployment endpoint | replica 와 revision, autoscaling 을 가진 모델 서빙 단위입니다. | endpoint |   |
| 배포 프리셋 | deployment preset | runtime variant 하나에 대한 이름 있는 템플릿으로 deployment 의 시작 값을 담습니다. |   |   |
| 배포 전략 | deployment strategy | deployment 의 리비전을 배포하는 방식으로 ROLLING, BLUE_GREEN 값을 가집니다. |   |   |
| 도메인 | domain | project 와 user 를 담는 최상위 tenant 입니다. |   |   |
| 에러 로그 | error log | 사용자에게 노출되어 읽음 처리하거나 지울 수 있는 오류 기록입니다. | 오류 로그 |   |
| fair share | fair share | 사용 이력에 따라 자원을 공평하게 배분하는 스케줄링 기능입니다. |   |   |
| fair share 계수 | fair share factor | 지난 사용량을 반영해 계산되며 값이 높을수록 스케줄링 우선순위가 높은 지표입니다. | Fairness Score, 우선 순위 계수 |   |
| GPU 분할 | fractional GPU sharing | enterprise 버전에서만 쓸 수 있는 GPU 나눠 쓰기 기능입니다. | GPU sharing, fractional sharing of GPUs, GPU 분할 공유 |   |
| 데스크톱 클라이언트 | GUI desktop client | 웹에서 불가능한 GUI 기능을 쓰게 해주는 데스크톱 클라이언트입니다. | Backend.AI Web UI App |   |
| 허깅 페이스 레지스트리 | HuggingFace registry | HuggingFace Hub 주소와 접근 token 을 담은 registry 항목입니다. | HuggingFace 레지스트리 |   |
| 유휴 검사기 | idle checker | 수명, 네트워크 무응답, 자원 사용률 기준으로 session 을 종료하는 규칙입니다. |   |   |
| 이미지 | image | 세션을 띄우는 container image 로 registry 에 속합니다. |   |   |
| 이미지 별칭 | image alias | 이미지에 붙이는 별칭으로 등록과 해제는 superadmin 검사로 보호됩니다. | 별명 |   |
| 기본 제공 서비스 | intrinsic service | 이미지 저자가 따로 지원하지 않아도 모든 kernel 에서 쓸 수 있는 서비스입니다. |   |   |
| 커널 | kernel | 세션 을 실행하는 container 입니다. |   |   |
| 커널 그룹 | kernel group | session 의 한 role 로 속한 kernel 들이 하나의 execution spec 을 공유하는 단위입니다. |   |   |
| 커널 그룹 역할 | kernel group role | 클러스터 세션에서 kernel 이 맡는 역할로 첫 컨테이너가 main, 나머지가 sub 입니다. | cluster role, 클러스터 역할 |   |
| 로그인 클라이언트 유형 | login client type | login session 을 여는 client 의 종류입니다. |   |   |
| 로그인 이력 | login history | 사용자에 대해 기록된 login 시도 하나입니다. |   |   |
| 로그인 세션 | login session | 사용자가 인증한 상태로 남는 session 이며 active, invalidated, revoked 값을 가집니다. |   |   |
| 모델 카드 | model card | vfolder 에 담긴 model 에 대한 설명입니다. |   |   |
| 모델 정의 | model definition | model service 의 model 구성과 메타데이터를 정의하는 설정입니다. |   |   |
| 모델 리비전 | model revision | model deployment 안에서 모델의 불변 버전입니다. |   |   |
| 모델 스토어 | model store | 사용자가 모델을 골라 자신의 vfolder 로 가져오는 스토어입니다. |   |   |
| 모델 스토어 프로젝트 | model store project | model card 가 속하는 MODEL_STORE project type 의 project 입니다. |   |   |
| 모델 vfolder | model vfolder | 모델 파라미터와 실행 구성 파일을 담은 vfolder 입니다. | 모델 폴더 |   |
| 멀티 커널 세션 | multi-kernel session | 여러 kernel 을 가진 세션입니다. | cluster session, 클러스터 세션 |   |
| 알림 채널 | notification channel | notification 을 보내는 대상입니다. |   |   |
| 알림 규칙 | notification rule | 한 종류의 event 를 channel 로 보내며 쓸 메시지를 정하는 규칙입니다. |   |   |
| 오브젝트 스토리지 | object storage | endpoint 와 자격 증명으로 접근하는 S3 호환 object storage 입니다. |   |   |
| 개인 프로젝트 | personal project | user 마다 하나만 두는 개인 project 입니다. |   |   |
| 파이프라인 | pipeline | 연산 작업을 이어서 설계·실행하는 단위입니다. |   |   |
| 프로젝트 | project | domain 안에서 session 과 vfolder 를 소유하는 사용자 묶음입니다. | group |   |
| 프로젝트 유형 | project type | project 의 용도와 동작을 정하는 종류입니다. |   |   |
| 프로메테우스 쿼리 프리셋 | prometheus query preset | 이름 붙은 Prometheus 질의 템플릿과 실행 시간 범위를 미리 저장해 둔 대상입니다. |   |   |
| 가용량 범위 | quota scope | 사용자별과 프로젝트별 스토리지 사용량 한도입니다. |   |   |
| 최대 요청수 | rate limit | client 가 서버에 과부하를 주지 않도록 API 요청 수를 제한하는 한도입니다. |   |   |
| 복제본 | replica | deployment 를 서비스하는 session 하나로, healthy 이면 트래픽의 일부를 받습니다. |   |   |
| 복제본 그룹 | replica group | deployment 의 replica 들을 묶어 리비전 사이를 옮겨가며 트래픽을 조정하는 단위입니다. |   |   |
| Reservoir | Reservoir | artifact 저장소로 쓰이는 artifact registry 종류입니다. | 리저버, 레저버 | 제품 이름이라 영어로만 씁니다 |
| 자원 할당 | resource allocation | 커널이 한 자원을 요청하고 받아 실제로 쓴 양을 기록하는 항목입니다. |   |   |
| 자원 그룹 | resource group | agent 를 묶어 독립된 scheduler 로 세션을 배치하는 단위입니다. | scaling group, sgroup, 리소스 그룹, 스케일링 그룹 |   |
| 자원 프리셋 | resource preset | session 이 요청할 수 있는 이름 있는 자원량 묶음입니다. | 리소스 프리셋 |   |
| 자원 슬롯 | resource slot | 세션에 할당되는 CPU, memory, GPU 등 자원 단위입니다. | 리소스 슬롯 |   |
| 자원 슬롯 유형 | resource slot type | resource slot 값의 형태 구분으로 count, bytes, unique, unified 값을 가집니다. | 리소스 슬롯 유형, 슬롯 타입 |   |
| 자원별 가중치 | resource weight | 자원 종류별로 두는 fair share 우선순위 배율입니다. |   |   |
| 리비전 | revision | deployment 의 구성 한 시점 스냅샷입니다. |   |   |
| 롤링 업데이트 | rolling update | deployment 가 새 revision 을 점진적으로 배포하는 방식입니다. |   |   |
| 인퍼런스 런타임 종류 | runtime variant | deployment revision 이 실행되는 model serving runtime 입니다. | 런타임, 런타임 변형, 변형 |   |
| 런타임 파라미터 | runtime variant preset | runtime variant 하나의 저장된 설정입니다. |   |   |
| 스케줄러 유형 | scheduler type | resource group 의 scheduler 종류입니다. |   |   |
| 스크래치 스토리지 | scratch storage | kernel 마다 주어지고 종료 시 정리되는 로컬 임시 저장 공간입니다. |   |   |
| 서비스 카탈로그 | service catalog | 실행 중인 컴포넌트가 manager 에 자신을 알려 등록되는 카탈로그입니다. | SD catalog |   |
| 서비스 그룹 | service group | service catalog 에서 같은 종류의 service instance 를 묶는 식별자입니다. |   |   |
| 서비스 포트 | service port | container 가 외부에 노출하는 서비스 포트입니다. | Service Proxies |   |
| 세션 | session | kernel 을 묶어 실행하는 단위입니다. 같은 실행 스펙을 가진 kernel 은 세션 안에서 kernel group 으로 관리합니다. | 계산 세션, compute session, 연산 세션, computing session |   |
| 세션 의존 관계 | session dependency | 다른 session 이 기다리는 session 간 의존 관계입니다. |   |   |
| 세션 그룹 | session group | 여러 세션을 같은 agent 에 모으거나 흩어 배치하는 단위입니다. | placement group |   |
| 세션 이력 | session history | 세션 스케줄링 handler 가 한 번 실행될 때 상태 변화와 결과를 남긴 기록입니다. |   |   |
| 세션 수명 | session lifetime | 세션이 실행될 수 있는 최대 시간입니다. |   |   |
| 세션 템플릿 | session template | 세션을 만들 때 쓰는 저장된 설정입니다. | task template |   |
| 세션 유형 | session type | session 의 종류 값 묶음으로 interactive, batch, inference, system 이 있습니다. | 세션 타입 |   |
| 스토리지 호스트 | storage host | vfolder 를 두는 storage backend host 입니다. |   |   |
| 스토리지 네임스페이스 | storage namespace | object storage 의 bucket 이나 VFS storage 의 subpath 입니다. | 네임스페이스 |   |
| 스토리지 볼륨 | storage volume | storage backend 위의 논리 볼륨으로 각 서비스가 선언한 이름으로 식별됩니다. |   |   |
| 시스템 세션 | system session | SFTP session 처럼 사용자가 띄우는 system 종류의 session 입니다. |   |   |
| 종료 | terminate | 세션을 끝내는 동작입니다. |   |   |
| unmanaged vfolder | unmanaged vfolder | storage host 의 경로를 그대로 가리키는 vfolder 로 unmanaged_path 에 그 경로를 둡니다. | unmanaged virtual folder, Unmanaged 폴더 |   |
| 사용자 | user | domain 안의 계정입니다. |   |   |
| 사용자 자원 정책 | user resource policy | user 단위로 적용되는 자원 한도 정책입니다. | 사용자 정책 |   |
| vfolder | vfolder | 사용자나 project 가 소유하고 container 에 실행 시 마운트되는 저장 공간입니다. | virtual folder, 가상 폴더, 폴더 | 일반 폴더와 다른 개념입니다 |
