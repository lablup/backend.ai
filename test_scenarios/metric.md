# Metric Service Test Scenarios

## 서비스 개요
Metric 서비스는 Backend.AI의 컨테이너 사용률 메트릭을 수집하고 관리합니다.
CPU, 메모리, 네트워크, 디스크 사용량 등의 시계열 데이터를 Prometheus 백엔드에서 조회하여 제공합니다.

## 주요 기능 목록
1. Query Metadata - 사용 가능한 메트릭 이름 조회
   - Action: `ContainerMetricMetadataAction`
   - Result: `ContainerMetricMetadataActionResult`
2. Query Metric - 시계열 메트릭 데이터 조회
   - Action: `ContainerMetricAction`
   - Result: `ContainerMetricActionResult`

## 테스트 시나리오

### 1. Query Metadata

#### 기능 설명
시스템에서 사용 가능한 메트릭 이름 목록을 조회합니다.

#### 테스트 케이스

##### 1.1 전체 메트릭 목록 조회
- **입력값**: 
  - 없음
- **기대 출력값**: 
  - 사용 가능한 모든 메트릭 이름 목록
  - 예: ["container_cpu_percent", "container_memory_used_bytes", "container_network_rx_bytes", ...]
- **동작 근거**: 
  - Prometheus API에서 메트릭 목록 가져오기

##### 1.2 Prometheus 연결 실패
- **입력값**: 
  - Prometheus 서버 다운
- **기대 출력값**: 
  - `MetricServiceUnavailable` 예외
- **동작 근거**: 
  - 백엔드 연결 상태 확인

##### 1.3 빈 메트릭 목록
- **입력값**: 
  - 메트릭이 수집되지 않은 새 시스템
- **기대 출력값**: 
  - 빈 배열 []
- **동작 근거**: 
  - 초기 시스템 상태

### 2. Query Metric

#### 기능 설명
특정 메트릭의 시계열 데이터를 조회합니다.

#### 테스트 케이스

##### 2.1 CPU 사용률 조회
- **입력값**: 
  - `metric_name`: "container_cpu_percent"
  - `start`: "2024-01-01T00:00:00"
  - `end`: "2024-01-01T01:00:00"
  - `step`: 60 (1분 간격)
  - `value_type`: "usage"
  - `labels`: {"kernel_id": "kernel-123"}
- **기대 출력값**: 
  - 시간별 CPU 사용률 데이터
  - 형식: [(timestamp1, value1), (timestamp2, value2), ...]
- **동작 근거**: 
  - 특정 커널의 CPU 사용률 추적

##### 2.2 메모리 사용량 RATE 조회
- **입력값**: 
  - `metric_name`: "container_memory_used_bytes"
  - `metric_type`: "RATE"
  - `start`: "2024-01-01T00:00:00"
  - `end`: "2024-01-01T00:05:00"
  - `rate_window`: 60
- **기대 출력값**: 
  - 메모리 사용량 변화율
  - 초당 바이트 증가/감소량
- **동작 근거**: 
  - 메모리 누수 감지

##### 2.3 네트워크 전송량 DIFF 조회
- **입력값**: 
  - `metric_name`: "container_network_tx_bytes"
  - `metric_type`: "DIFF"
  - `labels`: {"agent_id": "agent-1"}
  - `step`: 300 (5분)
- **기대 출력값**: 
  - 5분 간격 네트워크 전송량
  - 각 간격별 총 전송 바이트
- **동작 근거**: 
  - 네트워크 사용 패턴 분석

##### 2.4 프로젝트별 집계
- **입력값**: 
  - `metric_name`: "container_cpu_percent"
  - `aggregate_by`: "project"
  - `labels`: {"project": "research-team"}
- **기대 출력값**: 
  - 프로젝트 전체 CPU 사용률 합계
- **동작 근거**: 
  - 팀 단위 리소스 모니터링

##### 2.5 사용자별 GPU 사용률
- **입력값**: 
  - `metric_name`: "container_gpu_percent"
  - `aggregate_by`: "user"
  - `labels`: {"user_email": "user@example.com"}
  - `gpu_metric`: true
- **기대 출력값**: 
  - 사용자의 모든 GPU 사용률
  - GPU별 개별 데이터
- **동작 근거**: 
  - 사용자 GPU 할당량 추적

##### 2.6 잘못된 메트릭 이름
- **입력값**: 
  - `metric_name`: "invalid_metric_name"
- **기대 출력값**: 
  - 빈 결과 또는 `MetricNotFound` 예외
- **동작 근거**: 
  - 존재하지 않는 메트릭 처리

##### 2.7 시간 범위 초과
- **입력값**: 
  - `start`: "2023-01-01T00:00:00"
  - `end`: "2024-01-01T00:00:00" (1년)
  - `step`: 60
- **기대 출력값**: 
  - `TimeRangeTooLarge` 예외 또는 성능 경고
- **동작 근거**: 
  - 과도한 데이터 요청 방지

##### 2.8 레이블 필터링
- **입력값**: 
  - `labels`: {"agent_id": "agent-1", "kernel_id": "kernel-*"}
  - 와일드카드 패턴 사용
- **기대 출력값**: 
  - 특정 에이전트의 모든 커널 메트릭
- **동작 근거**: 
  - 유연한 필터링 지원

##### 2.9 용량 값 조회
- **입력값**: 
  - `metric_name`: "container_memory_capacity_bytes"
  - `value_type`: "capacity"
- **기대 출력값**: 
  - 할당된 메모리 용량 (변하지 않는 값)
- **동작 근거**: 
  - 사용량 대비 용량 비교

##### 2.10 메트릭 타입 자동 감지
- **입력값**: 
  - `metric_name`: "container_network_rx_bytes"
  - `metric_type`: null (자동)
- **기대 출력값**: 
  - 누적 카운터로 자동 인식
  - DIFF 타입으로 처리
- **동작 근거**: 
  - 메트릭 이름 기반 타입 추론

## 복합 시나리오

### 1. 다중 커널 세션 모니터링
- **상황**: 클러스터 세션의 모든 커널 모니터링
- **조회 순서**: 
  1. 세션의 모든 kernel_id 조회
  2. 각 커널별 CPU, 메모리 메트릭 조회
  3. 결과 집계 및 시각화
- **기대 결과**: 
  - 클러스터 전체 리소스 사용 패턴
  - 불균형 감지

### 2. 리소스 사용 추세 분석
- **상황**: 지난 24시간 리소스 사용 추세
- **조회 설정**: 
  - 5분 간격 데이터
  - CPU, 메모리, 디스크 동시 조회
- **기대 결과**: 
  - 피크 시간대 식별
  - 리소스 병목 지점 발견

### 3. 비용 계산을 위한 메트릭
- **상황**: 월별 사용량 기반 과금
- **조회 방법**: 
  - 시간별 평균값 계산
  - 프로젝트/사용자별 집계
- **기대 결과**: 
  - 정확한 리소스 사용 시간
  - 과금 가능한 데이터

## 성능 고려사항

### 쿼리 최적화
1. **적절한 step 크기**
   - 짧은 기간: 작은 step (30-60초)
   - 긴 기간: 큰 step (5-15분)
   - 자동 다운샘플링

2. **레이블 필터 우선**
   - 가능한 한 구체적인 레이블 지정
   - 와일드카드 최소화
   - 인덱스 활용

3. **시간 범위 제한**
   - 최대 7일 권장
   - 긴 기간은 집계된 데이터 사용

### 메트릭 타입별 특성
1. **GAUGE 타입**
   - 즉시값 (CPU %, 메모리 사용량)
   - 평균, 최대, 최소값 의미 있음

2. **COUNTER 타입**
   - 누적값 (네트워크 바이트, 디스크 I/O)
   - RATE 또는 DIFF로 변환 필요

3. **HISTOGRAM 타입**
   - 분포 데이터 (응답 시간)
   - 백분위수 계산 가능

## 공통 에러 케이스

### Prometheus 쿼리 에러
- **상황**: 잘못된 PromQL 구문
- **기대 동작**: 
  - 명확한 에러 메시지
  - 쿼리 수정 제안

### 메트릭 수집 지연
- **상황**: 최신 데이터 없음
- **기대 동작**: 
  - 마지막 수집 시간 표시
  - 데이터 갭 표시

### 레이블 불일치
- **상황**: 요청한 레이블 조합 없음
- **기대 동작**: 
  - 빈 결과 반환
  - 사용 가능한 레이블 제안

