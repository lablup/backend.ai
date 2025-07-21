# 코드 레이어 분리 후 동작 호환성 검증을 위한 테스트 코드 작성 기획서

## 프로젝트 개요

### 배경
- 클로드코드를 사용한 코드 레이어 분리 작업 완료

### 목표
각 도메인별로 테스트 시나리오를 기반으로 한 체계적인 동작 호환성 검증 및 테스트 코드 작성

## 작업 프로세스

* mock 을 사용하여 unit test 를 작성 필요. 
* src/ai/backend/manager/repositories/model_serving 패키지 내에 repository.py , admin_repository.py에 대한 레포지토리 레이어 유닛 테스트를 만들어야 함
* 테스트 코드는 tests/manager/repositories 패키지 내부에 생성
* 테스트를 만들 때는 메서드 별로 파일을 쪼개서 작성
* test/manager/services/model_serving 패키지 내부처럼 conftest에 공통적으로 사용되는 픽스쳐를 만들고 하위 패키지 내에 메서드 별 파일에서 주입하여 사용
* 메서드 동작을 모킹해야 하는 경우 test/manager/services/model_serving 패키지 내부에 있는 테스트 처럼 patch를 하는 fixture를 만들고 주입하는 방식으로 작성


# 이번에 작업할 범위

* src/ai/backend/manager/repositories/model_serving 패키지에 대해서만 위의 작업 프로세스를 진행할 것

## 작업 방식

* 작업이 중단되었다면, step.md 파일을 확인하여 중단된 작업부터 이어서 진행할 것

1. 이번에 작업할 범위에 대해서만 작업을 수행함
2. 작업을 수행하기 전 단계별로 step.md 파일에 수행해야할 작업을 작성
3. 작업을 완료하면 step.md 파일에 완료한 작업을 작성
4. 모든 작업이 완료되면 다음 동작 확인
    * pants lint :: 를 실행하여 lint 오류가 없는지 확인
    * pants fmt :: 를 실행하여 코드 포맷이 일관된지 확인
    * pants check :: 를 실행하여 코드 품질이 유지되는지 확인
    * pants test :: 를 실행하여 테스트가 모두 통과하는지 확인