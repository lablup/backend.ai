## 참고 코드

* repository 동작 권장사항은 src/ai/backend/manager/repositories/image 패키지의 코드 구현을 참고
* 서비스 동작에서의 권장사항은 src/ai/backend/manager/services/image/service.py 패키지의 코드 구현을 참고

## Repository Layer 분리 작업 가이드라인 (다른 도메인 적용 시)

### 1. Repository 구조 설계
* 기본 Repository와 AdminRepository를 분리
    * 일반 사용자용: 권한 검증이 포함된 메소드
    * 관리자용(AdminRepository): 권한 검증을 건너뛰는 메소드
        * service layer에서 SUPERADMIN 권한을 체크해 동작하는 메소드가 있을 경우에만 생성
    * 상속은 사용하지 않음

### 2. Service Layer 수정
* Service 생성자에서 Repository와 AdminRepository 모두 주입받도록 수정
* 권한에 따른 Repository 사용 패턴:
    ```python
    if action.client_role == UserRole.SUPERADMIN:
        data = await self._admin_repository.method_force(...)
    else:
        data = await self._repository.method_validated(...)
    ```
* 조건문에서 이미 return한 경우 else 생략 (early return pattern)

### 3. 타입 시스템 개선
* Repository 메소드는 Row 객체가 아닌 Dataclass 반환
* Optional 타입은 `typing.Optional` 사용
* None 체크는 early return 패턴 적용
* async with 블록 외부에서 반환하여 lazy loading 방지

### 4. 성능 최적화
* 하나의 서비스 동작에서 repository 메소드를 여러 횟수 서비스에서 호출하는 경우 repository 메소드를 따로 만들어 DB를 여러번 접근하지 않도록 최적화
* 여러 번의 DB 호출을 하나로 통합할 수 있는 경우 batch 메소드 구현
    * 예: `resolve_images_batch()` - 여러 이미지를 한 번에 조회

### 5. Private 메소드 패턴
* 자주 사용되는 DB 작업은 SASession을 받는 private 메소드로 구현
    * `_get_by_id(session: SASession, id: UUID)`
    * `_validate_ownership(session: SASession, id: UUID, user_id: UUID)`
* 이를 통해 코드 재사용성 향상 및 트랜잭션 관리 용이

### 6. Exception 처리
* Service 전용 Exception이 Repository에서 필요한 경우:
    * `src/ai/backend/manager/errors/exceptions.py`로 이동
    * BackendError를 상속받아 구현
    * 적절한 HTTP 상태 코드 클래스도 함께 상속
* Repository는 도메인에 맞는 예외만 발생시킴

### 7. 메소드 반환 타입 일관성
* 단일 객체 조회: `Optional[DataClass]`
* 리스트 조회: `list[DataClass]`
* 생성/수정: `DataClass`
* 삭제 시 관련 정보가 필요한 경우: `tuple[UUID, DataClass]`

### 8. 의존성 주입
* `processors.py`에서 Repository와 AdminRepository 인스턴스 생성
* Service 생성 시 두 Repository 모두 주입
* 다른 서비스와의 의존성은 Service Layer에서만 처리

### 9. 코드 스타일
* import 순서: 표준 라이브러리 → 서드파티 → 로컬 모듈
* import 는 상위에서만 사용하고 TYPE_CHECKING 는 사용하지 않음
* `__init__.py`는 비워둠 (no `__all__` exports)
* 주석은 docstring 만 작성하고 코드 내 주석은 최소화

### 10. 트랜잭션 관리
* Repository 메소드는 하나의 트랜잭션으로 처리
* 복잡한 비즈니스 로직은 Service Layer에서 처리
* Repository는 순수한 데이터 접근 로직만 포함

## 이번 작업 범위

* `src/ai/backend/manager/services/image/service.py` 파일의 service layer 에서 DB 관련 동작을 repository layer로 분리
    * `src/ai/backend/manager/repositories` 패키지에 새로운 repository directory 와 Repository file 생성

## 구현 이후
* 구현이 모두 마무리 되면 다음 순서로 확인
    * `pants fix ::` 를 통해 코드 스타일을 자동으로 수정
    * `pants lint ::` 를 통해 코드 스타일을 확인
    * `pants check ::` 를 통해 타입 체크를 수행
    * `pants test ::` 를 통해 테스트를 수행

