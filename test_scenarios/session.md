# Session Service Test Scenarios

## 서비스 개요
Session 서비스는 Backend.AI의 핵심 서비스로, 컴퓨팅 세션의 전체 생명주기를 관리합니다.
세션 생성, 실행, 파일 관리, 서비스 관리, 모니터링 등 포괄적인 기능을 제공합니다.

## 주요 기능 목록

### 세션 생성 및 관리
1. Create from Params - 매개변수로 세션 생성
   - Action: `CreateFromParamsAction`
   - Result: `CreateFromParamsActionResult`
2. Create from Template - 템플릿으로 세션 생성
   - Action: `CreateFromTemplateAction`
   - Result: `CreateFromTemplateActionResult`
3. Create Cluster - 클러스터 세션 생성
   - Action: `CreateClusterAction`
   - Result: `CreateClusterActionResult`
4. Modify Session - 세션 속성 수정
   - Action: `ModifySessionAction`
   - Result: `ModifySessionActionResult`
5. Rename Session - 세션 이름 변경
   - Action: `RenameSessionAction`
   - Result: `RenameSessionActionResult`

### 세션 생명주기 제어
6. Execute Session - 세션에서 코드 실행
   - Action: `ExecuteSessionAction`
   - Result: `ExecuteSessionActionResult`
7. Interrupt - 실행 중인 작업 중단
   - Action: `InterruptSessionAction`
   - Result: `InterruptSessionActionResult`
8. Restart Session - 세션 재시작
   - Action: `RestartSessionAction`
   - Result: `RestartSessionActionResult`
9. Destroy Session - 세션 종료
   - Action: `DestroySessionAction`
   - Result: `DestroySessionActionResult`
10. Check and Transit Status - 상태 확인 및 전환
   - Action: `CheckAndTransitStatusAction`
   - Result: `CheckAndTransitStatusActionResult`

### 코드 완성 및 AI 기능
11. Complete - 코드 자동완성
   - Action: `CompleteAction`
   - Result: `CompleteActionResult`
12. Commit Session - 세션 상태 저장
   - Action: `CommitSessionAction`
   - Result: `CommitSessionActionResult`

### 파일 관리
13. List Files - 파일 목록 조회
   - Action: `ListFilesAction`
   - Result: `ListFilesActionResult`
14. Upload Files - 파일 업로드
   - Action: `UploadFilesAction`
   - Result: `UploadFilesActionResult`
15. Download File - 단일 파일 다운로드
   - Action: `DownloadFileAction`
   - Result: `DownloadFileActionResult`
16. Download Files - 다중 파일 다운로드
   - Action: `DownloadFilesAction`
   - Result: `DownloadFilesActionResult`

### 서비스 관리
17. Start Service - 서비스 시작
   - Action: `StartServiceAction`
   - Result: `StartServiceActionResult`
18. Shutdown Service - 서비스 종료
   - Action: `ShutdownServiceAction`
   - Result: `ShutdownServiceActionResult`

### 세션 정보 및 모니터링
19. Get Session Info - 세션 정보 조회
   - Action: `GetSessionInfoAction`
   - Result: `GetSessionInfoActionResult`
20. Get Status History - 상태 변경 이력
   - Action: `GetStatusHistoryAction`
   - Result: `GetStatusHistoryActionResult`
21. Get Container Logs - 컨테이너 로그 조회
   - Action: `GetContainerLogsAction`
   - Result: `GetContainerLogsActionResult`
22. Get Abusing Report - 리소스 남용 보고서
   - Action: `GetAbusingReportAction`
   - Result: `GetAbusingReportActionResult`
23. Get Commit Status - 커밋 상태 확인
   - Action: `GetCommitStatusAction`
   - Result: `GetCommitStatusActionResult`
24. Get Direct Access Info - 직접 접근 정보
   - Action: `GetDirectAccessInfoAction`
   - Result: `GetDirectAccessInfoActionResult`
25. Get Dependency Graph - 의존성 그래프
   - Action: `GetDependencyGraphAction`
   - Result: `GetDependencyGraphActionResult`
26. Match Sessions - 세션 검색
   - Action: `MatchSessionsAction`
   - Result: `MatchSessionsActionResult`

### 고급 기능
27. Convert Session to Image - 세션을 이미지로 변환
   - Action: `ConvertSessionToImageAction`
   - Result: `ConvertSessionToImageActionResult`

## 테스트 시나리오

### 1. Create from Params

#### 기능 설명
명시적인 매개변수를 사용하여 새로운 세션을 생성합니다.

#### 테스트 케이스

##### 1.1 단일 GPU 세션 생성
- **입력값**: 
  - `image_name`: "tensorflow:2.10-gpu"
  - `session_name`: "my-tf-session"
  - `resources`: {"cpu": "4", "memory": "16G", "gpu": "1"}
  - `vfolders`: ["home", "data"]
  - `scaling_group`: "gpu-cluster"
- **기대 출력값**: 
  - 세션 ID
  - 상태: PENDING → SCHEDULED → RUNNING
- **동작 근거**: 
  - 리소스 할당 및 스케줄링 성공

##### 1.2 리소스 부족
- **입력값**: 
  - `resources`: {"cpu": "1000", "memory": "10TB"}
- **기대 출력값**: 
  - `QuotaExceeded` 예외
- **동작 근거**: 
  - 사용자 리소스 정책 초과

##### 1.3 존재하지 않는 이미지
- **입력값**: 
  - `image_name`: "non-existent:latest"
- **기대 출력값**: 
  - `ImageNotFound` 예외
- **동작 근거**: 
  - 유효한 이미지만 사용 가능

##### 1.4 환경 변수 설정
- **입력값**: 
  - `env`: {"CUDA_VISIBLE_DEVICES": "0", "PYTHONPATH": "/app"}
  - `secret_env`: {"API_KEY": "secret-value"}
- **기대 출력값**: 
  - 환경 변수가 설정된 세션
- **동작 근거**: 
  - 일반 및 비밀 환경 변수 지원

##### 1.5 부팅 스크립트
- **입력값**: 
  - `bootstrap_script`: "pip install -r requirements.txt\npython setup.py"
- **기대 출력값**: 
  - 세션 시작 시 스크립트 실행
- **동작 근거**: 
  - 초기화 작업 자동화

### 2. Create from Template

#### 기능 설명
미리 정의된 템플릿을 사용하여 세션을 생성합니다.

#### 테스트 케이스

##### 2.1 템플릿 기반 생성
- **입력값**: 
  - `template_id`: "ml-workspace"
  - `overrides`: {"session_name": "custom-name"}
- **기대 출력값**: 
  - 템플릿 설정이 적용된 세션
- **동작 근거**: 
  - 표준화된 환경 제공

##### 2.2 템플릿 오버라이드
- **입력값**: 
  - `template_id`: "basic-python"
  - `overrides`: {"resources": {"cpu": "8"}}
- **기대 출력값**: 
  - 템플릿 기본값 + 오버라이드 적용
- **동작 근거**: 
  - 유연한 커스터마이징

##### 2.3 존재하지 않는 템플릿
- **입력값**: 
  - `template_id`: "non-existent-template"
- **기대 출력값**: 
  - `TemplateNotFound` 예외
- **동작 근거**: 
  - 유효한 템플릿만 사용

### 3. Create Cluster

#### 기능 설명
다중 노드 클러스터 세션을 생성합니다.

#### 테스트 케이스

##### 3.1 MPI 클러스터 생성
- **입력값**: 
  - `cluster_mode`: "mpi"
  - `cluster_size`: 4
  - `image_name`: "mpi-python:latest"
- **기대 출력값**: 
  - 메인 노드 + 워커 노드 3개
  - MPI 통신 설정 완료
- **동작 근거**: 
  - 분산 컴퓨팅 지원

##### 3.2 단일 노드 클러스터
- **입력값**: 
  - `cluster_mode`: "single-node"
  - `cluster_size`: 1
- **기대 출력값**: 
  - 단일 세션 생성
- **동작 근거**: 
  - 클러스터 모드 호환성

##### 3.3 리소스 불균형
- **입력값**: 
  - `cluster_size`: 10
  - 사용 가능한 노드: 3
- **기대 출력값**: 
  - `InsufficientResources` 예외
- **동작 근거**: 
  - 전체 클러스터 생성 보장

### 4. Execute Session

#### 기능 설명
실행 중인 세션에서 코드를 실행합니다.

#### 테스트 케이스

##### 4.1 Python 코드 실행
- **입력값**: 
  - `session_id`: "running-session-id"
  - `run_id`: "run-123"
  - `code`: "print('Hello, World!')\nresult = 2 + 2"
  - `mode`: "query"
- **기대 출력값**: 
  - `stdout`: "Hello, World!\n"
  - `result`: {"result": 4}
- **동작 근거**: 
  - 코드 실행 및 출력 캡처

##### 4.2 에러 발생
- **입력값**: 
  - `code`: "1 / 0"
- **기대 출력값**: 
  - `stderr`: "ZeroDivisionError"
  - `exit_code`: 1
- **동작 근거**: 
  - 에러 처리 및 반환

##### 4.3 긴 실행 시간
- **입력값**: 
  - `code`: "import time; time.sleep(60)"
  - `timeout`: 10
- **기대 출력값**: 
  - `ExecutionTimeout` 예외
- **동작 근거**: 
  - 타임아웃 제어

##### 4.4 대화형 입력
- **입력값**: 
  - `code`: "name = input('Enter name: ')"
  - `stdin`: "Alice\n"
- **기대 출력값**: 
  - 입력 처리 완료
- **동작 근거**: 
  - 대화형 실행 지원

### 5. Interrupt

#### 기능 설명
실행 중인 작업을 중단합니다.

#### 테스트 케이스

##### 5.1 실행 중인 코드 중단
- **입력값**: 
  - `session_id`: "running-session-id"
  - `run_id`: "long-running-123"
- **기대 출력값**: 
  - 실행 중단됨
  - `KeyboardInterrupt` 시그널
- **동작 근거**: 
  - 즉시 중단 지원

##### 5.2 이미 완료된 실행
- **입력값**: 
  - `run_id`: "completed-run"
- **기대 출력값**: 
  - 성공 (멱등성)
- **동작 근거**: 
  - 중복 중단 요청 처리

### 6. List Files

#### 기능 설명
세션 내의 파일 목록을 조회합니다.

#### 테스트 케이스

##### 6.1 디렉토리 목록
- **입력값**: 
  - `session_id`: "valid-session-id"
  - `path`: "/home/work"
- **기대 출력값**: 
  - 파일 및 디렉토리 목록
  - 각 항목의 메타데이터 (크기, 권한, 수정일)
- **동작 근거**: 
  - 파일 시스템 탐색

##### 6.2 숨김 파일 포함
- **입력값**: 
  - `path`: "/home"
  - `show_hidden`: true
- **기대 출력값**: 
  - `.bashrc`, `.profile` 등 포함
- **동작 근거**: 
  - 전체 파일 시스템 뷰

##### 6.3 존재하지 않는 경로
- **입력값**: 
  - `path`: "/non/existent/path"
- **기대 출력값**: 
  - `PathNotFound` 예외
- **동작 근거**: 
  - 유효한 경로만 접근

### 7. Upload Files

#### 기능 설명
세션에 파일을 업로드합니다.

#### 테스트 케이스

##### 7.1 단일 파일 업로드
- **입력값**: 
  - `files`: [{"name": "data.csv", "content": "...", "size": 1024}]
  - `path`: "/home/work"
- **기대 출력값**: 
  - 업로드 성공
  - 파일 생성 확인
- **동작 근거**: 
  - 파일 전송 지원

##### 7.2 다중 파일 업로드
- **입력값**: 
  - `files`: 10개 파일
  - 총 크기: 5MB
- **기대 출력값**: 
  - 모든 파일 업로드 성공
- **동작 근거**: 
  - 배치 업로드 지원

##### 7.3 파일 수 초과
- **입력값**: 
  - `files`: 21개 파일
- **기대 출력값**: 
  - `TooManyFiles` 예외
- **동작 근거**: 
  - 20개 파일 제한

##### 7.4 파일 크기 초과
- **입력값**: 
  - `files`: [{"size": 2 * 1024 * 1024}]
- **기대 출력값**: 
  - `FileTooLarge` 예외
- **동작 근거**: 
  - 파일당 1MB 제한

### 8. Start Service

#### 기능 설명
세션 내에서 웹 서비스를 시작합니다.

#### 테스트 케이스

##### 8.1 Jupyter 노트북 시작
- **입력값**: 
  - `session_id`: "valid-session-id"
  - `app_name`: "jupyter"
  - `port`: 8888
- **기대 출력값**: 
  - 서비스 URL
  - 접근 토큰
- **동작 근거**: 
  - 웹 IDE 지원

##### 8.2 사용자 정의 앱
- **입력값**: 
  - `app_name`: "custom-web-app"
  - `args`: {"port": 5000}
- **기대 출력값**: 
  - 커스텀 서비스 실행
- **동작 근거**: 
  - 유연한 서비스 지원

##### 8.3 포트 충돌
- **입력값**: 
  - 이미 사용 중인 포트 지정
- **기대 출력값**: 
  - 자동으로 다른 포트 할당
- **동작 근거**: 
  - 포트 충돌 해결

##### 8.4 지원하지 않는 앱
- **입력값**: 
  - `app_name`: "unsupported-app"
- **기대 출력값**: 
  - `AppNotFound` 예외
- **동작 근거**: 
  - 등록된 앱만 실행

### 9. Get Container Logs

#### 기능 설명
세션 컨테이너의 로그를 조회합니다.

#### 테스트 케이스

##### 9.1 전체 로그 조회
- **입력값**: 
  - `session_id`: "valid-session-id"
  - `kernel_id`: null (모든 커널)
- **기대 출력값**: 
  - stdout/stderr 로그
  - 타임스탬프 포함
- **동작 근거**: 
  - 디버깅 지원

##### 9.2 특정 커널 로그
- **입력값**: 
  - `kernel_id`: "specific-kernel-id"
- **기대 출력값**: 
  - 해당 커널의 로그만
- **동작 근거**: 
  - 클러스터 세션 지원

##### 9.3 로그 필터링
- **입력값**: 
  - `since`: "2024-01-01T00:00:00"
  - `until`: "2024-01-01T01:00:00"
- **기대 출력값**: 
  - 시간 범위 내 로그
- **동작 근거**: 
  - 로그 검색 효율성

### 10. Convert Session to Image

#### 기능 설명
실행 중인 세션을 재사용 가능한 이미지로 변환합니다.

#### 테스트 케이스

##### 10.1 세션 이미지 생성
- **입력값**: 
  - `session_id`: "customized-session"
  - `image_name`: "my-custom-env:v1"
  - `registry`: "private-registry"
- **기대 출력값**: 
  - 이미지 빌드 시작
  - 레지스트리에 푸시
- **동작 근거**: 
  - 환경 재사용성

##### 10.2 대용량 세션
- **입력값**: 
  - 세션 크기: 10GB
- **기대 출력값**: 
  - 진행 상황 리포팅
  - 타임아웃 없이 완료
- **동작 근거**: 
  - 대용량 이미지 처리

##### 10.3 레지스트리 권한 없음
- **입력값**: 
  - `registry`: "unauthorized-registry"
- **기대 출력값**: 
  - `RegistryPushError` 예외
- **동작 근거**: 
  - 레지스트리 접근 제어

### 11. Check and Transit Status

#### 기능 설명
세션 상태를 확인하고 필요시 전환합니다.

#### 테스트 케이스

##### 11.1 정상 상태 전환
- **입력값**: 
  - `session_id`: "pending-session"
  - Dead 세션 임계값 도달
- **기대 출력값**: 
  - PENDING → ERROR 전환
- **동작 근거**: 
  - 자동 상태 관리

##### 11.2 배치 상태 확인
- **입력값**: 
  - `session_ids`: ["session1", "session2", "session3"]
- **기대 출력값**: 
  - 각 세션의 상태 업데이트
- **동작 근거**: 
  - 효율적인 배치 처리

## 공통 에러 케이스

### 세션 상태 불일치
- **상황**: 세션이 예상과 다른 상태
- **기대 동작**: 
  - `InvalidSessionState` 예외
  - 현재 상태 정보 제공

### 에이전트 연결 실패
- **상황**: 세션이 실행 중인 에이전트 다운
- **기대 동작**: 
  - `AgentNotAvailable` 예외
  - 자동 복구 시도

### 리소스 정책 위반
- **상황**: 할당된 리소스 초과 사용
- **기대 동작**: 
  - 경고 또는 세션 종료
  - 남용 보고서 생성

