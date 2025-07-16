# Resource Preset Service Test Scenarios

## 서비스 개요
Resource Preset 서비스는 Backend.AI에서 컴퓨팅 세션 생성 시 사용할 수 있는 리소스 할당 템플릿을 관리합니다.
사용자가 쉽게 적절한 리소스를 선택할 수 있도록 미리 정의된 CPU, 메모리, GPU 등의 조합을 제공합니다.

## 주요 기능 목록
1. Create Preset - 새로운 리소스 프리셋 생성
   - Action: `CreateResourcePresetAction`
   - Result: `CreateResourcePresetActionResult`
2. Modify Preset - 기존 프리셋 수정
   - Action: `ModifyResourcePresetAction`
   - Result: `ModifyResourcePresetActionResult`
3. Delete Preset - 프리셋 삭제
   - Action: `DeleteResourcePresetAction`
   - Result: `DeleteResourcePresetActionResult`
4. List Presets - 사용 가능한 프리셋 목록 조회
   - Action: `ListPresetsAction`
   - Result: `ListPresetsActionResult`
5. Check Presets - 프리셋 할당 가능성 및 리소스 사용량 확인
   - Action: `CheckPresetsAction`
   - Result: `CheckPresetsActionResult`

## 테스트 시나리오

### 1. Create Preset

#### 기능 설명
새로운 리소스 프리셋을 생성합니다.

#### 테스트 케이스

##### 1.1 CPU 전용 프리셋 생성
- **입력값**: 
  - `name`: "cpu-small"
  - `resource_slots`: {"cpu": "2", "memory": "4G"}
  - `shared_memory`: "1G"
  - `scaling_group_name`: null (글로벌)
- **기대 출력값**: 
  - 생성된 프리셋 정보
  - ID와 타임스탬프 포함
- **동작 근거**: 
  - 기본 CPU 작업용 프리셋

##### 1.2 GPU 프리셋 생성
- **입력값**: 
  - `name`: "gpu-standard"
  - `resource_slots`: {"cpu": "4", "memory": "16G", "gpu": "1", "gpu_memory": "8G"}
  - `shared_memory`: "2G"
  - `scaling_group_name`: "gpu-cluster"
- **기대 출력값**: 
  - GPU 클러스터 전용 프리셋 생성
- **동작 근거**: 
  - 스케일링 그룹별 프리셋 지원

##### 1.3 필수 리소스 누락
- **입력값**: 
  - `name`: "invalid-preset"
  - `resource_slots`: {"gpu": "1"} (CPU, 메모리 누락)
- **기대 출력값**: 
  - `InvalidResourceSlots` 예외
  - "intrinsic slots (cpu, memory) missing"
- **동작 근거**: 
  - CPU와 메모리는 필수

##### 1.4 중복된 프리셋 이름 (글로벌)
- **입력값**: 
  - `name`: "existing-preset"
  - `scaling_group_name`: null
- **기대 출력값**: 
  - `ResourcePresetConflict` 예외
- **동작 근거**: 
  - 글로벌 프리셋 이름은 고유

##### 1.5 중복된 프리셋 이름 (다른 스케일링 그룹)
- **입력값**: 
  - `name`: "common-preset"
  - `scaling_group_name`: "cluster-b" (cluster-a에 같은 이름 존재)
- **기대 출력값**: 
  - 성공적으로 생성
- **동작 근거**: 
  - 스케일링 그룹별로 이름 공간 분리

##### 1.6 커스텀 리소스 타입
- **입력값**: 
  - `resource_slots`: {"cpu": "4", "memory": "8G", "npu": "2", "tpu": "1"}
- **기대 출력값**: 
  - 커스텀 리소스 타입 포함 프리셋
- **동작 근거**: 
  - 확장 가능한 리소스 타입

### 2. Modify Preset

#### 기능 설명
기존 리소스 프리셋을 수정합니다.

#### 테스트 케이스

##### 2.1 리소스 슬롯 업데이트
- **입력값**: 
  - `preset_id_or_name`: "cpu-small"
  - `props`: {"resource_slots": {"cpu": "4", "memory": "8G"}}
- **기대 출력값**: 
  - 업데이트된 프리셋 정보
- **동작 근거**: 
  - 리소스 요구사항 변경

##### 2.2 프리셋 이름 변경
- **입력값**: 
  - `preset_id_or_name`: UUID("valid-preset-id")
  - `props`: {"name": "cpu-medium"}
- **기대 출력값**: 
  - 이름이 변경된 프리셋
- **동작 근거**: 
  - 프리셋 재명명 지원

##### 2.3 공유 메모리 조정
- **입력값**: 
  - `preset_id_or_name`: "gpu-standard"
  - `props`: {"shared_memory": "4G"}
- **기대 출력값**: 
  - 공유 메모리만 업데이트
- **동작 근거**: 
  - 부분 업데이트 지원

##### 2.4 필수 리소스 제거 시도
- **입력값**: 
  - `props`: {"resource_slots": {"gpu": "2"}} (CPU, 메모리 제거)
- **기대 출력값**: 
  - `InvalidResourceSlots` 예외
- **동작 근거**: 
  - 필수 리소스 유지

##### 2.5 존재하지 않는 프리셋
- **입력값**: 
  - `preset_id_or_name`: "non-existent-preset"
- **기대 출력값**: 
  - `ObjectNotFound` 예외
- **동작 근거**: 
  - 유효한 프리셋만 수정

### 3. Delete Preset

#### 기능 설명
리소스 프리셋을 삭제합니다.

#### 테스트 케이스

##### 3.1 정상적인 프리셋 삭제
- **입력값**: 
  - `preset_id_or_name`: "unused-preset"
- **기대 출력값**: 
  - 삭제된 프리셋 정보
- **동작 근거**: 
  - 사용하지 않는 프리셋 정리

##### 3.2 사용 중인 프리셋 삭제
- **입력값**: 
  - `preset_id_or_name`: "popular-preset" (활성 세션이 사용 중)
- **기대 출력값**: 
  - 삭제 성공 (세션은 영향 없음)
- **동작 근거**: 
  - 프리셋은 템플릿일 뿐


##### 3.4 UUID로 삭제
- **입력값**: 
  - `preset_id_or_name`: UUID("valid-preset-id")
- **기대 출력값**: 
  - 해당 프리셋 삭제
- **동작 근거**: 
  - ID와 이름 모두 지원

### 4. List Presets

#### 기능 설명
사용 가능한 리소스 프리셋 목록을 조회합니다.

#### 테스트 케이스

##### 4.1 전체 프리셋 목록
- **입력값**: 
  - `scaling_group`: null
- **기대 출력값**: 
  - 모든 글로벌 프리셋
  - 각 프리셋의 ID, 이름, 리소스 정보
- **동작 근거**: 
  - 전체 목록 조회

##### 4.2 스케일링 그룹별 필터링
- **입력값**: 
  - `scaling_group`: "gpu-cluster"
- **기대 출력값**: 
  - 글로벌 프리셋 + gpu-cluster 전용 프리셋
- **동작 근거**: 
  - 스케일링 그룹 컨텍스트

##### 4.3 리소스 슬롯 정규화
- **입력값**: 
  - 다양한 형식의 리소스 값 포함 프리셋
- **기대 출력값**: 
  - 정규화된 JSON 형식
  - 일관된 단위 표현
- **동작 근거**: 
  - 클라이언트 호환성

##### 4.4 빈 프리셋 목록
- **입력값**: 
  - 프리셋이 없는 시스템
- **기대 출력값**: 
  - 빈 배열 []
- **동작 근거**: 
  - 초기 시스템 상태

### 5. Check Presets

#### 기능 설명
프리셋의 할당 가능성과 현재 리소스 사용량을 확인합니다.

#### 테스트 케이스

##### 5.1 충분한 리소스 상황
- **입력값**: 
  - `keypair`: 유효한 키페어
  - `scaling_group`: "default"
- **기대 출력값**: 
  - 모든 프리셋 allocatable: true
  - 현재 사용량 정보
  - 남은 리소스 정보
- **동작 근거**: 
  - 리소스 여유 있음

##### 5.2 리소스 부족 상황
- **입력값**: 
  - 거의 모든 GPU 사용 중
  - GPU 프리셋 확인
- **기대 출력값**: 
  - GPU 프리셋 allocatable: false
  - CPU 프리셋 allocatable: true
  - 상세한 리소스 부족 이유
- **동작 근거**: 
  - 실시간 리소스 체크

##### 5.3 다층 리소스 제한
- **입력값**: 
  - 키페어, 그룹, 도메인 각각 제한 존재
- **기대 출력값**: 
  - 각 레벨별 리소스 사용량
  - 가장 제한적인 레벨 표시
  - 할당 가능한 프리셋 정확히 계산
- **동작 근거**: 
  - 계층적 리소스 관리

##### 5.4 에이전트 슬롯 부족
- **입력값**: 
  - CPU/메모리는 충분
  - 에이전트 슬롯 부족
- **기대 출력값**: 
  - allocatable: false
  - "No agent slots available"
- **동작 근거**: 
  - 물리적 제약 확인

##### 5.5 그룹 리소스 정보 숨김
- **입력값**: 
  - `group_resource_visibility`: false 설정
- **기대 출력값**: 
  - 개인 리소스 정보만 표시
  - 그룹 정보는 null 또는 숨김
- **동작 근거**: 
  - 프라이버시 설정

##### 5.6 동시 세션 제한
- **입력값**: 
  - max_concurrent_sessions: 3
  - 현재 실행 중: 3
- **기대 출력값**: 
  - 모든 프리셋 allocatable: false
  - "Session limit reached"
- **동작 근거**: 
  - 세션 수 제한


## 공통 에러 케이스

### 데이터베이스 무결성
- **상황**: 프리셋 이름 중복
- **기대 동작**: 
  - 고유 제약조건 위반 에러
  - 명확한 에러 메시지

### 리소스 타입 검증
- **상황**: 잘못된 리소스 타입
- **기대 동작**: 
  - 타입 검증 실패
  - 지원되는 타입 목록 제공

### 트랜잭션 처리
- **상황**: 프리셋 수정 중 에러
- **기대 동작**: 
  - 트랜잭션 롤백
  - 원래 상태 유지

