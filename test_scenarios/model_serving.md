# Model Serving Service Test Scenarios

## 서비스 개요
Model Serving 서비스는 Backend.AI에서 기계학습 모델의 배포와 서빙을 관리합니다.
모델 엔드포인트 생성, 자동 스케일링, 라우팅 관리, 접근 제어 등의 기능을 제공합니다.

## 주요 기능 목록

### 모델 서비스 관리
1. Create Model Service - 새로운 모델 서비스 배포
   - Action: `CreateModelServiceAction`
   - Result: `CreateModelServiceActionResult`
2. List Model Service - 배포된 모델 서비스 목록
   - Action: `ListModelServiceAction`
   - Result: `ListModelServiceActionResult`
3. Delete Model Service - 모델 서비스 삭제
   - Action: `DeleteModelServiceAction`
   - Result: `DeleteModelServiceActionResult`
4. Dry Run Model Service - 모델 서비스 테스트 배포
   - Action: `DryRunModelServiceAction`
   - Result: `DryRunModelServiceActionResult`
5. Get Model Service Info - 모델 서비스 상세 정보
   - Action: `GetModelServiceInfoAction`
   - Result: `GetModelServiceInfoActionResult`
6. Modify Endpoint - 엔드포인트 설정 변경
   - Action: `ModifyEndpointAction`
   - Result: `ModifyEndpointActionResult`

### 라우팅 및 스케일링
7. Scale Service Replicas - 서비스 복제본 수 조정
   - Action: `ScaleServiceReplicasAction`
   - Result: `ScaleServiceReplicasActionResult`
8. Update Route - 트래픽 라우팅 업데이트
   - Action: `UpdateRouteAction`
   - Result: `UpdateRouteActionResult`
9. Delete Route - 라우트 제거
   - Action: `DeleteRouteAction`
   - Result: `DeleteRouteActionResult`
10. Force Sync - AppProxy와 강제 동기화
   - Action: `ForceSyncAction`
   - Result: `ForceSyncActionResult`

### 자동 스케일링
11. Create Auto Scaling Rule - 자동 스케일링 규칙 생성
   - Action: `CreateAutoScalingRuleAction`
   - Result: `CreateAutoScalingRuleActionResult`
12. Modify Auto Scaling Rule - 자동 스케일링 규칙 수정
   - Action: `ModifyAutoScalingRuleAction`
   - Result: `ModifyAutoScalingRuleActionResult`
13. Delete Auto Scaling Rule - 자동 스케일링 규칙 삭제
   - Action: `DeleteAutoScalingRuleAction`
   - Result: `DeleteAutoScalingRuleActionResult`

### 접근 제어 및 오류 관리
14. Generate Token - 인증 토큰 생성
   - Action: `GenerateTokenAction`
   - Result: `GenerateTokenActionResult`
15. List Errors - 오류 목록 조회
   - Action: `ListErrorsAction`
   - Result: `ListErrorsActionResult`
16. Clear Error - 오류 상태 초기화
   - Action: `ClearErrorAction`
   - Result: `ClearErrorActionResult`

## 테스트 시나리오

### 1. Create Model Service

#### 기능 설명
VFolder에 저장된 모델을 서비스로 배포합니다.

#### 테스트 케이스

##### 1.1 정상적인 모델 배포
- **입력값**: 
  - `model_name`: "sentiment-analyzer"
  - `model_version`: "v1.0"
  - `vfolder_id`: UUID("model-vfolder-id")
  - `runtime_variant`: "custom"
  - `resource_slots`: {"cpu": "2", "memory": "4G"}
  - `resource_group`: "default"
  - `replicas`: 2
  - `public`: false
- **기대 출력값**: 
  - 생성된 엔드포인트 정보
  - 서비스 URL
  - 초기 상태: PROVISIONING
- **동작 근거**: 
  - 표준 모델 배포 프로세스

##### 1.2 모델 정의 파일 검증
- **입력값**: 
  - `vfolder_id`: VFolder with model-definition.toml
  - TOML 파일 내용 검증
- **기대 출력값**: 
  - 모델 설정 파싱 성공
  - 필수 필드 확인
- **동작 근거**: 
  - 유효한 모델 정의 필요

##### 1.3 리소스 부족
- **입력값**: 
  - `resource_slots`: {"cpu": "100", "memory": "1TB"}
  - `replicas`: 10
- **기대 출력값**: 
  - `InsufficientResources` 예외
- **동작 근거**: 
  - 리소스 가용성 확인

##### 1.4 중복 모델 이름
- **입력값**: 
  - `model_name`: "existing-model"
  - `model_version`: "v1.0"
- **기대 출력값**: 
  - `ModelAlreadyExists` 예외
- **동작 근거**: 
  - 고유한 모델-버전 조합

##### 1.5 퍼블릭 엔드포인트 생성
- **입력값**: 
  - `public`: true
  - `desired_session_count`: 3
- **기대 출력값**: 
  - 공개 접근 가능 URL
  - 로드밸런서 설정
- **동작 근거**: 
  - 외부 접근 허용

### 2. Dry Run Model Service

#### 기능 설명
실제 배포 없이 모델 서비스 설정을 검증합니다.

#### 테스트 케이스

##### 2.1 설정 검증
- **입력값**: 
  - 모델 서비스 설정
  - `dry_run`: true
- **기대 출력값**: 
  - 검증 결과
  - 예상 리소스 사용량
  - 설정 오류 (있을 경우)
- **동작 근거**: 
  - 배포 전 사전 검증

##### 2.2 모델 파일 누락
- **입력값**: 
  - VFolder without required model files
- **기대 출력값**: 
  - `ModelFileNotFound` 에러
  - 누락된 파일 목록
- **동작 근거**: 
  - 필수 파일 확인

### 3. Scale Service Replicas

#### 기능 설명
서비스 복제본 수를 수동으로 조정합니다.

#### 테스트 케이스

##### 3.1 스케일 업
- **입력값**: 
  - `endpoint_id`: UUID("running-endpoint")
  - `target_replicas`: 5 (현재 2)
- **기대 출력값**: 
  - 새 복제본 생성 시작
  - 상태: SCALING
- **동작 근거**: 
  - 부하 증가 대응

##### 3.2 스케일 다운
- **입력값**: 
  - `endpoint_id`: UUID("running-endpoint")
  - `target_replicas`: 1 (현재 5)
- **기대 출력값**: 
  - 복제본 종료 시작
  - 연결 드레이닝
- **동작 근거**: 
  - 리소스 절약

##### 3.3 제로 스케일
- **입력값**: 
  - `target_replicas`: 0
- **기대 출력값**: 
  - 모든 복제본 종료
  - 엔드포인트는 유지
- **동작 근거**: 
  - 일시적 서비스 중단

##### 3.4 리소스 한계 초과
- **입력값**: 
  - `target_replicas`: 100
- **기대 출력값**: 
  - `ResourceLimitExceeded` 예외
- **동작 근거**: 
  - 클러스터 용량 제한

### 4. Create Auto Scaling Rule

#### 기능 설명
메트릭 기반 자동 스케일링 규칙을 생성합니다.

#### 테스트 케이스

##### 4.1 CPU 기반 스케일링
- **입력값**: 
  - `endpoint_id`: UUID("model-endpoint")
  - `metric`: "cpu_utilization"
  - `threshold`: 70
  - `min_replicas`: 2
  - `max_replicas`: 10
  - `scale_up_delay`: 60
  - `scale_down_delay`: 300
- **기대 출력값**: 
  - 자동 스케일링 규칙 생성
  - 모니터링 시작
- **동작 근거**: 
  - CPU 사용률 기반 확장

##### 4.2 요청 수 기반 스케일링
- **입력값**: 
  - `metric`: "requests_per_second"
  - `threshold`: 100
  - `target_per_replica`: 50
- **기대 출력값**: 
  - RPS 기반 스케일링 설정
- **동작 근거**: 
  - 처리량 기반 확장

##### 4.3 커스텀 메트릭
- **입력값**: 
  - `metric`: "queue_length"
  - `metric_source`: "custom"
- **기대 출력값**: 
  - 커스텀 메트릭 모니터링
- **동작 근거**: 
  - 애플리케이션 특화 스케일링

##### 4.4 충돌하는 규칙
- **입력값**: 
  - 동일 엔드포인트에 다른 규칙 존재
- **기대 출력값**: 
  - `ConflictingRules` 예외
- **동작 근거**: 
  - 단일 규칙만 허용

### 5. Update Route

#### 기능 설명
서비스 인스턴스 간 트래픽 라우팅을 업데이트합니다.

#### 테스트 케이스

##### 5.1 가중치 기반 라우팅
- **입력값**: 
  - `endpoint_id`: UUID("model-endpoint")
  - `routes`: [
      {"instance_id": "inst-1", "weight": 70},
      {"instance_id": "inst-2", "weight": 30}
    ]
- **기대 출력값**: 
  - 트래픽 분배 업데이트
  - 70:30 비율로 라우팅
- **동작 근거**: 
  - A/B 테스팅 지원

##### 5.2 카나리 배포
- **입력값**: 
  - `routes`: [
      {"instance_id": "stable", "weight": 95},
      {"instance_id": "canary", "weight": 5}
    ]
- **기대 출력값**: 
  - 5% 트래픽만 신규 버전
- **동작 근거**: 
  - 안전한 롤아웃

##### 5.3 블루-그린 전환
- **입력값**: 
  - 모든 트래픽을 새 버전으로
- **기대 출력값**: 
  - 즉시 전환
  - 이전 버전은 대기
- **동작 근거**: 
  - 빠른 롤백 가능

### 6. Generate Token

#### 기능 설명
모델 엔드포인트 접근을 위한 인증 토큰을 생성합니다.

#### 테스트 케이스

##### 6.1 일반 토큰 생성
- **입력값**: 
  - `endpoint_id`: UUID("private-endpoint")
  - `expiry`: 86400 (24시간)
  - `scope`: "inference"
- **기대 출력값**: 
  - JWT 토큰
  - 만료 시간 포함
- **동작 근거**: 
  - 보안 접근 제어

##### 6.2 무제한 토큰
- **입력값**: 
  - `expiry`: null
  - `scope`: "admin"
- **기대 출력값**: 
  - 만료 없는 토큰
  - 관리자 권한
- **동작 근거**: 
  - 서비스 간 통신

##### 6.3 제한된 범위
- **입력값**: 
  - `scope`: "read-only"
  - `allowed_ips`: ["192.168.1.0/24"]
- **기대 출력값**: 
  - 읽기 전용 토큰
  - IP 제한 적용
- **동작 근거**: 
  - 세밀한 접근 제어

### 7. List Errors

#### 기능 설명
모델 서비스의 오류 이력을 조회합니다.

#### 테스트 케이스

##### 7.1 최근 오류 조회
- **입력값**: 
  - `endpoint_id`: UUID("failing-endpoint")
  - `limit`: 10
- **기대 출력값**: 
  - 최근 10개 오류
  - 타임스탬프, 오류 유형, 메시지
- **동작 근거**: 
  - 디버깅 지원

##### 7.2 오류 유형별 필터
- **입력값**: 
  - `error_type`: "OOMKilled"
- **기대 출력값**: 
  - 메모리 부족 오류만
- **동작 근거**: 
  - 특정 문제 추적

### 8. Get Model Service Info

#### 기능 설명
모델 서비스의 상세 정보를 조회합니다.

#### 테스트 케이스

##### 8.1 전체 정보 조회
- **입력값**: 
  - `endpoint_id`: UUID("running-endpoint")
- **기대 출력값**: 
  - 엔드포인트 URL
  - 현재 상태
  - 실행 중인 복제본
  - 리소스 사용량
  - 설정 정보
- **동작 근거**: 
  - 서비스 모니터링

##### 8.2 메트릭 포함
- **입력값**: 
  - `include_metrics`: true
- **기대 출력값**: 
  - 요청 수
  - 평균 응답 시간
  - 오류율
- **동작 근거**: 
  - 성능 모니터링

## 복합 시나리오

### 1. 모델 버전 업그레이드
1. 새 버전 배포 (카나리)
2. 트래픽 점진적 이동
3. 메트릭 모니터링
4. 문제 없으면 전체 전환
5. 이전 버전 제거

### 2. 장애 복구
1. 오류 감지 (health check 실패)
2. 자동 재시작 시도
3. 실패 시 이전 버전 롤백
4. 알림 발송

### 3. 비용 최적화
1. 사용량 패턴 분석
2. 자동 스케일링 규칙 조정
3. 유휴 시간 제로 스케일
4. 스케줄 기반 스케일링

## 공통 에러 케이스

### 모델 로딩 실패
- **상황**: 모델 파일 손상 또는 호환성 문제
- **기대 동작**: 
  - 명확한 오류 메시지
  - 롤백 옵션 제공

### 리소스 경합
- **상황**: GPU 메모리 부족
- **기대 동작**: 
  - 대기열 관리
  - 우선순위 기반 스케줄링

### 네트워크 장애
- **상황**: AppProxy 연결 실패
- **기대 동작**: 
  - 자동 재연결
  - 서비스 연속성 유지

