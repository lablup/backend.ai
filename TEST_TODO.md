# 코드 레이어 분리 후 동작 호환성 검증을 위한 테스트 코드 작성 기획서

## 프로젝트 개요

### 배경
- 클로드코드를 사용한 코드 레이어 분리 작업 완료
- 기존 동작 호환성 문제 발생
- 이전 버전 코드(_legacy.py)와 현재 버전 비교를 통한 동작 검증 필요

### 목표
각 도메인별로 테스트 시나리오를 기반으로 한 체계적인 동작 호환성 검증 및 테스트 코드 작성

## 작업 프로세스

### 1단계: 테스트 시나리오 분석 및 서비스 구현 비교
**입력**: `test_scenario/{service}.md`
**대상**: 현재 서비스 구현체
- `src/ai/backend/manager/services/{domain}/service.py` (일반적인 경우)
- `src/ai/backend/manager/services/{domain}/service/{sub_domain}.py` (세분화된 경우)

**작업 내용**:
- 테스트 시나리오 요구사항 분석
- 현재 서비스 구현체의 동작 방식 검토
- 호환성 여부 판단

### 2단계: 호환성 검증 결과에 따른 분기 처리

#### 2-1. 호환성 만족 시: 테스트 코드 작성
**출력 위치**: `tests/services/{domain}/test_{sub_domain}.py`
- sub_domain이 없는 경우: `test_{domain}.py`

**테스트 코드 구성**:
- 이전 버전(_legacy.py) 코드를 기반으로 한 테스트 케이스를 읽고 테스트 시나리오에 맞게 테스트 코드를 작성할 것
- 현재 구현체와의 동작 비교 검증
- 주요 기능별 단위 테스트
    - 테스트 작성은 기존에 작성되어있던 `tests/manager/services/test_users.py` 파일을 참고하여 작성
    - @pytest.mark.parametrize 와 TestScenario 클래스를 활용하여 테스트 케이스를 작성

#### 2-2. 호환성 불만족 시: 수정 사항 문서화
**출력 위치**: `NEED_TO_CHANGE.md`

**문서 내용**:
- 호환성 문제가 발생한 서비스 로직 식별
- 구체적인 수정 필요 사항
- 우선순위 및 영향도 분석

### 3단계: 서비스 동작 시나리오 문서화
**출력 위치**: `src/ai/backend/manager/services/{domain}/README.md`
**언어**: 영어

**문서 구성**:
- Service Overview
- Key Features and Capabilities
- Operation Scenarios
- API Usage Examples
- Integration Points
- Testing Guidelines

## 파일 구조 및 명명 규칙

### 기존 파일 구조
```
src/ai/backend/manager/services/{domain}/
├── service.py (또는 service/{sub_domain}.py)
└── service_legacy.py (또는 service/{sub_domain}_legacy.py)
```

### 테스트 파일 구조
```
tests/services/{domain}/
└── test_{sub_domain}.py (또는 test_{domain}.py)
```

### 문서 파일 구조
```
test_scenario/{service}.md
NEED_TO_CHANGE.md
src/ai/backend/manager/services/{domain}/README.md
```

## 품질 보증 기준

### 테스트 코드 품질 기준
- 테스트 커버리지 80% 이상
- 모든 주요 기능에 대한 단위 테스트 포함
- 에러 케이스 및 경계 조건 테스트
- 이전 버전과의 동작 일치성 검증

### 문서화 품질 기준
- 명확하고 구체적인 문제 설명
- 실행 가능한 해결 방안 제시
- 코드 예시 및 사용법 포함

## 성공 지표

1. **호환성 검증 완료율**: 모든 도메인에 대한 검증 완료
2. **테스트 코드 작성률**: 호환성을 만족하는 서비스에 대한 테스트 코드 100% 작성
3. **문제 식별률**: 호환성 문제 발생 서비스에 대한 수정 사항 100% 문서화
4. **문서화 완료율**: 모든 도메인에 대한 README.md 작성 완료

# 이번에 작업할 범위

* src/ai/backend/manager/services/agent 패키지에 대해서만 위의 작업 프로세스를 진행할 것

## 작업 방식

1. 이번에 작업할 범위에 대해서만 작업을 수행함
2. 작업을 수행하기 전 단계별로 step.md 파일에 수행해야할 작업을 작성
3. 작업을 완료하면 step.md 파일에 완료한 작업을 작성
4. 모든 작업이 완료되면 다음 동작 확인
    * pants lint :: 를 실행하여 lint 오류가 없는지 확인
    * pants fmt :: 를 실행하여 코드 포맷이 일관된지 확인
    * pants check :: 를 실행하여 코드 품질이 유지되는지 확인
    * pants test :: 를 실행하여 테스트가 모두 통과하는지 확인
