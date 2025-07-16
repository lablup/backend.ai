# Agent Service Test Scenarios

## 서비스 개요
Agent 서비스는 Backend.AI 클러스터의 에이전트들을 관리하고 제어하는 서비스입니다. 
각 에이전트의 watcher 프로세스를 통해 에이전트의 시작, 중지, 재시작 등의 작업을 수행하고, 
에이전트의 상태를 모니터링하며, 리소스 사용량을 계산하는 기능을 제공합니다.

## 주요 기능 목록
1. Sync Agent Registry - 에이전트의 커널 레지스트리 동기화
   - Action: `SyncAgentRegistryAction`
   - Result: `SyncAgentRegistryActionResult`
2. Get Watcher Status - 에이전트 watcher의 상태 확인
   - Action: `GetWatcherStatusAction`
   - Result: `GetWatcherStatusActionResult`
3. Watcher Agent Start - 에이전트 시작
   - Action: `WatcherAgentStartAction`
   - Result: `WatcherAgentStartActionResult`
4. Watcher Agent Stop - 에이전트 중지
   - Action: `WatcherAgentStopAction`
   - Result: `WatcherAgentStopActionResult`
5. Watcher Agent Restart - 에이전트 재시작
   - Action: `WatcherAgentRestartAction`
   - Result: `WatcherAgentRestartActionResult`
6. Recalculate Usage - 전체 에이전트의 리소스 사용량 재계산
   - Action: `RecalculateUsageAction`
   - Result: `RecalculateUsageActionResult`

## 테스트 시나리오

### 1. Sync Agent Registry

#### 기능 설명
특정 에이전트의 커널 레지스트리 정보를 동기화하고 업데이트된 에이전트 정보를 반환합니다.

#### 테스트 케이스

##### 1.1 정상적인 동기화
- **입력값**: 
  - `agent_id`: 유효한 에이전트 ID (예: "agent-123")
- **기대 출력값**: 
  - 동기화된 에이전트의 데이터베이스 row 정보
  - AgentRow 객체의 모든 필드가 포함됨
- **동작 근거**: 
  - AgentRegistry.sync_agent_kernel_registry()가 성공적으로 실행
  - 데이터베이스에서 해당 에이전트 정보 조회 가능

##### 1.2 존재하지 않는 에이전트
- **입력값**: 
  - `agent_id`: 존재하지 않는 에이전트 ID (예: "invalid-agent")
- **기대 출력값**: 
  - Exception 또는 None
- **동작 근거**: 
  - 데이터베이스에 해당 에이전트가 존재하지 않음

### 2. Get Watcher Status

#### 기능 설명
에이전트의 watcher 프로세스 상태를 확인합니다.

#### 테스트 케이스

##### 2.1 정상 동작하는 watcher
- **입력값**: 
  - `agent_id`: 유효한 에이전트 ID
- **기대 출력값**: 
  - HTTP 200 응답
  - watcher의 상태 정보 (JSON 형태)
- **동작 근거**: 
  - etcd에서 에이전트 IP와 watcher 포트 정보 조회 성공
  - watcher 프로세스가 정상 동작 중
  - 5초 내에 응답

##### 2.2 응답하지 않는 watcher
- **입력값**: 
  - `agent_id`: watcher가 응답하지 않는 에이전트 ID
- **기대 출력값**: 
  - Timeout 에러 (5초 타임아웃)
- **동작 근거**: 
  - watcher 프로세스가 중단되었거나 네트워크 문제

##### 2.3 잘못된 인증 토큰
- **입력값**: 
  - `agent_id`: 유효한 에이전트 ID
  - 잘못된 watcher 토큰 설정
- **기대 출력값**: 
  - HTTP 401 Unauthorized 응답
- **동작 근거**: 
  - X-BackendAI-Watcher-Token 헤더 검증 실패

### 3. Watcher Agent Start

#### 기능 설명
에이전트를 시작합니다.

#### 테스트 케이스

##### 3.1 정상적인 에이전트 시작
- **입력값**: 
  - `agent_id`: 중지된 상태의 에이전트 ID
- **기대 출력값**: 
  - HTTP 200 응답
  - 시작 확인 메시지
- **동작 근거**: 
  - watcher가 에이전트 프로세스 시작 명령 실행 성공
  - 20초 내에 시작 완료

##### 3.2 이미 실행 중인 에이전트
- **입력값**: 
  - `agent_id`: 이미 실행 중인 에이전트 ID
- **기대 출력값**: 
  - HTTP 409 Conflict 또는 특정 에러 메시지
- **동작 근거**: 
  - 에이전트가 이미 실행 중이므로 시작할 수 없음

##### 3.3 시작 실패 (리소스 부족)
- **입력값**: 
  - `agent_id`: 유효한 에이전트 ID
  - 시스템 리소스 부족 상황
- **기대 출력값**: 
  - HTTP 500 에러 또는 특정 에러 메시지
- **동작 근거**: 
  - 시스템 리소스 부족으로 프로세스 시작 실패

### 4. Watcher Agent Stop

#### 기능 설명
에이전트를 중지합니다.

#### 테스트 케이스

##### 4.1 정상적인 에이전트 중지
- **입력값**: 
  - `agent_id`: 실행 중인 에이전트 ID
- **기대 출력값**: 
  - HTTP 200 응답
  - 중지 확인 메시지
- **동작 근거**: 
  - watcher가 에이전트 프로세스 중지 명령 실행 성공
  - 20초 내에 중지 완료

##### 4.2 이미 중지된 에이전트
- **입력값**: 
  - `agent_id`: 이미 중지된 에이전트 ID
- **기대 출력값**: 
  - HTTP 409 Conflict 또는 성공 응답
- **동작 근거**: 
  - 이미 중지된 상태이므로 중복 작업

##### 4.3 실행 중인 커널이 있는 에이전트
- **입력값**: 
  - `agent_id`: 실행 중인 커널이 있는 에이전트 ID
- **기대 출력값**: 
  - HTTP 409 Conflict 또는 강제 중지 옵션 필요 메시지
- **동작 근거**: 
  - 실행 중인 커널이 있을 때 중지 정책

### 5. Watcher Agent Restart

#### 기능 설명
에이전트를 재시작합니다.

#### 테스트 케이스

##### 5.1 정상적인 에이전트 재시작
- **입력값**: 
  - `agent_id`: 실행 중인 에이전트 ID
- **기대 출력값**: 
  - HTTP 200 응답
  - 재시작 확인 메시지
- **동작 근거**: 
  - watcher가 에이전트 중지 후 시작 명령 실행 성공
  - 20초 내에 재시작 완료

##### 5.2 중지된 에이전트 재시작
- **입력값**: 
  - `agent_id`: 중지된 상태의 에이전트 ID
- **기대 출력값**: 
  - HTTP 200 응답 (시작과 동일한 효과)
- **동작 근거**: 
  - 중지된 상태에서는 시작만 수행

##### 5.3 재시작 중 타임아웃
- **입력값**: 
  - `agent_id`: 재시작에 시간이 오래 걸리는 에이전트 ID
- **기대 출력값**: 
  - Timeout 에러 (20초 타임아웃)
- **동작 근거**: 
  - 에이전트 재시작이 20초 내에 완료되지 않음

### 6. Recalculate Usage

#### 기능 설명
모든 에이전트의 리소스 사용량을 재계산합니다.

#### 테스트 케이스

##### 6.1 정상적인 사용량 재계산
- **입력값**: 없음
- **기대 출력값**: 
  - 성공 메시지 또는 None
  - 모든 에이전트의 리소스 사용량 업데이트
- **동작 근거**: 
  - AgentRegistry.recalc_resource_usage() 성공적으로 실행

##### 6.2 에이전트가 없는 경우
- **입력값**: 없음 (에이전트가 등록되지 않은 상태)
- **기대 출력값**: 
  - 성공 (아무 작업 없이 완료)
- **동작 근거**: 
  - 재계산할 에이전트가 없으므로 즉시 완료

##### 6.3 일부 에이전트 오류
- **입력값**: 없음 (일부 에이전트가 응답하지 않는 상태)
- **기대 출력값**: 
  - 부분 성공 또는 경고 메시지
  - 응답하는 에이전트들의 사용량만 업데이트
- **동작 근거**: 
  - 전체 실패가 아닌 부분 실패 허용

## 공통 에러 케이스

### etcd 연결 실패
- **상황**: etcd 서버에 연결할 수 없음
- **기대 동작**: 
  - etcd 연결 에러 발생
  - 에이전트 정보 조회 불가

### 데이터베이스 연결 실패
- **상황**: 데이터베이스에 연결할 수 없음
- **기대 동작**: 
  - 데이터베이스 연결 에러 발생
  - 에이전트 정보 조회 불가

### 네트워크 장애
- **상황**: 에이전트와 manager 간 네트워크 장애
- **기대 동작**: 
  - HTTP 요청 타임아웃
  - 연결 에러 발생

