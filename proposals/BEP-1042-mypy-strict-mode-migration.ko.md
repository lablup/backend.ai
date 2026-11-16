# MyPy strict mode 마이그레이션

## 관련 이슈

- JIRA Epic: [BA-4169](https://lablup.atlassian.net/browse/BA-4169) - MyPy strict mode 마이그레이션
  - [BA-4170](https://lablup.atlassian.net/browse/BA-4170) - 우선순위 1: unused-coroutine(20)
  - [BA-4171](https://lablup.atlassian.net/browse/BA-4171) - 우선순위 2: comparison-overlap(61)
  - [BA-4172](https://lablup.atlassian.net/browse/BA-4172) - 우선순위 3: call-arg(33)
  - [BA-4173](https://lablup.atlassian.net/browse/BA-4173) - 우선순위 4: arg-type(170)
  - [BA-4174](https://lablup.atlassian.net/browse/BA-4174) - 우선순위 5: assignment(33)
  - [BA-4175](https://lablup.atlassian.net/browse/BA-4175) - 우선순위 6: attr-defined(29)
  - [BA-4176](https://lablup.atlassian.net/browse/BA-4176) - 우선순위 7: union-attr(23)
  - [BA-4177](https://lablup.atlassian.net/browse/BA-4177) - 우선순위 8: return-value(5)
- GitHub: 없음

## 동기

Backend.AI 프로젝트는 지금 MyPy 로 타입 검사를 하지만 strict mode 를 활성화하지 않는다.

### 문제

1. **타입 안전성 부족**
   - `ignore_missing_imports = true` 가 외부 라이브러리의 타입 검사를 우회한다
   - generic 타입 인자(`Task`, `dict`, `list` 등)가 없다
   - 함수와 메서드에 타입 annotation 이 없다

2. **실제 버그 가능성**
   - `await` 누락으로 coroutine 이 실행되지 않는다(20건)
   - 논리적으로 불가능한 비교가 있다(61건)
   - 타입 불일치로 실행 시 에러가 날 수 있다(293건)

3. **코드 품질 저하**
   - 불필요한 `# type: ignore` 주석이 있다(300건)
   - 타입 검사가 우회되어 IDE 자동 완성이 제한된다
   - 리팩터링 중 타입 에러를 일찍 발견할 수 없다

### 현재 상태 분석

MyPy strict mode 를 활성화하면 **총 4,547개 에러**가 검출된다.

| 에러 유형 | 건수 | 위험도 | 주된 원인 |
|-----------|-------|-----------|---------------|
| no-untyped-def | 1,380 | 낮음 | 타입 annotation 누락 |
| type-arg | 1,120 | 중하 | generic 타입 인자 누락 |
| no-any-return | 469 | 중하 | Any 타입 반환 |
| misc | 466 | 중 | 기타 타입 에러 |
| unused-ignore | 300 | 낮음 | 불필요한 주석 |
| arg-type | 170 | 높음 | 인자 타입 불일치 |
| no-untyped-call | 149 | 중 | 타입 없는 함수 호출 |
| import-untyped | 133 | 중하 | 타입 정보 없는 import |
| **고위험 에러** | **374** | **높음** | **실행 시 에러 가능성** |

**테스트와 production 비율**(고위험 에러 374건):

- 테스트 코드: 358(96%)
- production 코드: 16(4%)

## 현재 설계

### MyPy 설정(pyproject.toml)

```toml
[tool.mypy]
plugins = ["pydantic.mypy", "strawberry.ext.mypy_plugin"]
ignore_missing_imports = true
follow_untyped_imports = false
implicit_reexport = false
mypy_path = "stubs:src"
namespace_packages = true
explicit_package_bases = true
python_executable = "dist/export/python/virtualenvs/python-default/3.13.7/bin/python"
disable_error_code = ["typeddict-unknown-key"]
```

### 문제

1. **완화된 설정**
   - `ignore_missing_imports = true`: 외부 라이브러리 타입을 무시한다
   - 일부 모듈은 에러 코드를 완전히 비활성화한다

2. **불완전한 타입 적용 범위**
   - stub 파일이 불완전하다(trafaret 등)
   - generic 타입 인자가 없다
   - 함수 signature 가 불완전하다

## 제안 설계

### 1단계: strict mode 활성화(즉시)

```toml
[tool.mypy]
plugins = ["pydantic.mypy", "strawberry.ext.mypy_plugin"]
strict = true  # Add this
mypy_path = "stubs:src"
namespace_packages = true
explicit_package_bases = true
python_executable = "dist/export/python/virtualenvs/python-default/3.13.7/bin/python"
disable_error_code = ["typeddict-unknown-key"]
```

strict mode 가 자동으로 활성화하는 옵션:

- `warn_unused_configs = true`
- `disallow_any_generics = true`
- `disallow_untyped_defs = true`
- `warn_redundant_casts = true`
- `warn_unused_ignores = true`
- `no_implicit_reexport = true`(이미 설정됨)
- 이 외에 11개 옵션

### 2단계: 고위험 에러 수정(우선순위 기준)

8개 우선순위로 분류한 에러 374건을 수정한다.

#### 우선순위 1: unused-coroutine(20건) 🔴 치명적

**위험도**: 함수가 실행되지 않음
**난이도**: 매우 낮음
**예상 시간**: 1~2시간

```python
# Before
session.Manager.freeze()  # Coroutine not executed

# After
await session.Manager.freeze()
```

**영향 파일**: 5개(모두 테스트 파일)

---

#### 우선순위 2: comparison-overlap(61건) 🔴 높음

**위험도**: 조건이 항상 false
**난이도**: 중하
**예상 시간**: 3~4시간

##### 2.1 test_docker.py 집중(20건)
```python
# Before
result = ImageRef.from_image_str(...)
assert result.tag_set == ("3.6", {"ubuntu"})  # Type mismatch

# After
result: ImageRef = ImageRef.from_image_str(...)
assert result.tag_set == ("3.6-ubuntu", set())
```

##### 2.2 Path 와 "-" 비교(12건, production 포함)
```python
# Before
if output == "-":  # Path vs str

# After
if str(output) == "-":
```

##### 2.3 Enum 과 문자열(5건)
```python
# Before
if user_role == UserRole.ADMIN or user_role == "admin":

# After
if user_role == UserRole.ADMIN:
```

---

#### 우선순위 3: call-arg(33건) 🟠 높음

**위험도**: 실행 시 TypeError
**난이도**: 낮음
**예상 시간**: 2~3시간

##### 3.1 LoggingConfig 필수 인자(26건)
```python
# Option 1: Fixture pattern
@pytest.fixture
def minimal_logging_config() -> LoggingConfig:
    return LoggingConfig(
        version=1,
        level=LogLevel.INFO,
        disable_existing_loggers=False,
        handlers={},
        loggers={},
    )

# Option 2: Type ignore (temporary)
logging_config = LoggingConfig()  # type: ignore[call-arg]
```

---

#### 우선순위 4: arg-type(170건) 🟠 중상

**위험도**: 실행 시 TypeError 가능성
**난이도**: 중하
**예상 시간**: 4~5시간

##### 4.1 test_argparse.py(18건)
```python
# Before
port_no(22)  # int → str

# After
port_no("22")
```

##### 4.2 도메인 타입 변환(10건)
```python
# Before
BaseActionResultMeta(
    action_id=None,  # UUID required
    status="pending",  # Enum required
)

# After
BaseActionResultMeta(
    action_id=uuid4(),
    status=OperationStatus.PENDING,
)
```

---

#### 우선순위 5: assignment(33건) 🟡 중간

**위험도**: 잘못된 타입 대입
**난이도**: 낮음
**예상 시간**: 2시간

```python
# Before
role_source: RoleSource = OperationType.CREATE  # Wrong enum

# After
role_source: RoleSource = RoleSource.USER_DEFINED
```

---

#### 우선순위 6: attr-defined(29건) 🟡 중간

**위험도**: AttributeError
**난이도**: 중간
**예상 시간**: 2~3시간

```python
# Before
a = host_port_pair("host:123")
assert a.host == "host"  # tuple has no .host

# After - Option 1: Use indexing
assert a[0] == "host"

# After - Option 2: NamedTuple
class HostPort(NamedTuple):
    host: str
    port: int
```

---

#### 우선순위 7: union-attr(23건) 🟡 중하

**위험도**: 일부 타입에서 AttributeError
**난이도**: 중간
**예상 시간**: 2~3시간

```python
# Before
event: QueueSentinel | Event = await queue.get()
assert event.key == "wow"  # QueueSentinel has no key

# After
if isinstance(event, Event):
    assert event.key == "wow"
```

---

#### 우선순위 8: return-value(5건) 🟠 높음(production)

**위험도**: production 코드의 타입 불일치
**난이도**: 높음
**예상 시간**: 2~3시간

```python
# Before
def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# After
from typing import TypeVar, ParamSpec, Callable

P = ParamSpec('P')
R = TypeVar('R')

def decorator(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper
```

### 3단계: 중위험 에러 수정(점진적)

나머지 4,173건을 우선순위 순으로 수정한다.

1. **type-arg**(1,120): generic 타입 인자 추가
2. **no-any-return**(469): Any 반환 제거
3. **no-untyped-call**(149): stub 파일 개선

### 4단계: 낮은 우선순위(장기)

1. **unused-ignore**(300): 불필요한 주석 제거
2. **redundant-cast**(72): 불필요한 cast 제거
3. **no-untyped-def**(1,380): 타입 annotation 추가

## 마이그레이션, 호환성

### 하위 호환성

✅ **동작 변경 없음**

- 타입 검사만 강화하고 실행 시 동작은 같다
- 기존 테스트가 통과함을 보장한다

✅ **점진적 마이그레이션**

- 각 단계를 독립적으로 수정할 수 있다
- rollback 전략을 준비한다

### 깨지는 변경

❌ **없음**

- 타입 검사 강제는 개발에만 영향을 준다
- 배포한 코드의 동작은 변경되지 않는다

### 마이그레이션 단계

1. **즉시**: MyPy strict mode 활성화(1단계)
2. **1주 이내**: 고위험 에러 374건 수정(2단계)
3. **1개월 이내**: 중위험 에러 수정(3단계)
4. **3개월 이내**: 낮은 우선순위 에러 수정(4단계)

## 구현 계획

### 1단계: 설정 변경(1일 차)

**작업**:

- `pyproject.toml` 에 `strict = true` 추가
- 전체 에러 보고서 생성
- 에러 분류와 우선순위 확정

**검증**:
```bash
pants check :: > mypy_strict_report.txt
```

---

### 2단계: 고위험 에러 수정(2~5일 차)

#### 2.1 빠른 수정(2일 차, 4시간)

**대상**: 42건
1. 우선순위 1: unused-coroutine(20)
2. 우선순위 2.2: Path 와 "-"(12)
3. 우선순위 2.3: Enum 과 문자열(5)
4. 우선순위 3.2: AccessKey 인자(5)

**검증**:
```bash
pants check tests/unit/client::
pants check src/ai/backend/cli::
```

**커밋**: `fix(mypy): Resolve critical errors (unused-coroutine, comparison-overlap)`

---

#### 2.2 집중 수정(3일 차, 6시간)

**대상**: 62건
1. 우선순위 2.1: test_docker.py(20)
2. 우선순위 3.1: LoggingConfig(26)
3. 우선순위 4.1: test_argparse.py(18)

**검증**:
```bash
pants check tests/unit/common/test_docker.py
pants check tests/unit::/conftest.py
```

**커밋**: `fix(mypy): Resolve test infrastructure errors`

---

#### 2.3 타입 정리(4일 차, 5시간)

**대상**: 32건
1. 우선순위 4.2: 도메인 타입(10)
2. 우선순위 5.1: Enum 대입(6)
3. 우선순위 6.2: tuple attribute(6)
4. 우선순위 7.1: QueueSentinel(12)

**검증**:
```bash
pants check tests/unit/manager/actions::
pants check tests/unit/common/test_etcd.py
```

**커밋**: `fix(mypy): Resolve type conversion and union errors`

---

#### 2.4 production 과 나머지(5일 차, 7시간)

**대상**: 238건
1. 우선순위 8: return-value production(5) ⚠️ 검토 필요
2. 우선순위 2.4: 기타 비교(24)
3. 남은 분산 에러

**검증**:
```bash
pants check src/ai/backend/agent/agent.py
pants check src/ai/backend/manager/api::
pants test --changed-since=HEAD~1  # Behavioral verification required
```

**커밋**: `fix(mypy): Resolve production code type errors`

---

### 3단계: 중위험 에러(1~2주)

**방식**: 매주 특정 에러 유형에 집중한다

**1주 차**: type-arg 에러
- generic 타입 인자 추가
- 목표: 1,120 → 500

**2주 차**: no-any-return, no-untyped-call
- Any 타입 제거
- stub 파일 개선
- 목표: 618 → 300

---

### 4단계: 낮은 우선순위(1~2개월)

**방식**: 리팩터링과 함께 점진적으로 개선한다

- 새 코드는 strict mode 를 준수해야 한다
- 기존 코드는 수정할 때 개선한다
- 목표: 점진적 감소

## 열린 질문

### Q1: LoggingConfig 기본값 처리

**질문**: LoggingConfig 에 이미 Field(default=...) 가 있는데 call-arg 에러가 나는 이유.

**후보 답변**:
- pydantic v2 strict mode 동작을 확인해야 한다
- MyPy plugin 이 기본값을 인식하지 못할 수 있다

**결정**: 2.2단계에서 실제 에러를 확인한 뒤 정한다.

---

### Q2: stub 파일 개선 범위

**질문**: trafaret 같은 외부 라이브러리의 stub 개선 범위가 남은 쟁점이다.

**후보 답변**:
- 방안 1: 최소 수정(현재 사용하는 API 만)
- 방안 2: 전체 구현(모든 API)
- 방안 3: 외부 프로젝트(typeshed)에 기여

**결정**: 3단계에서 실제 필요를 평가한 뒤 정한다.

---

### Q3: production decorator 수정 방식

**질문**: production decorator 의 return-value 에러 수정 방식이 남은 쟁점이다.

**후보 답변**:
- 방안 1: ParamSpec 사용(타입 안전, 복잡)
- 방안 2: type ignore(단순, 타입 안전성 낮음)
- 방안 3: decorator 재설계(완전하지만 오래 걸림)

**결정**: 2.4단계에서 사례별로 판단한다.

## 성공 기준

### 정량 목표

**2단계 이후**(고위험 에러):
- [ ] unused-coroutine: 0
- [ ] comparison-overlap: 0
- [ ] call-arg: 0
- [ ] arg-type: < 10
- [ ] assignment: 0
- [ ] attr-defined: < 5
- [ ] union-attr: < 5
- [ ] return-value: 0
- [ ] 기존 테스트 전부 통과

**3단계 이후**(중위험 에러):
- [ ] type-arg: < 500(현재 1,120)
- [ ] no-any-return: < 200(현재 469)
- [ ] no-untyped-call: < 50(현재 149)

**4단계 이후**(장기 목표):
- [ ] 전체 에러: < 1,000(현재 4,547)
- [ ] 새 코드의 타입 에러 0 유지

### 정성 목표

- [ ] IDE 타입 자동 완성 개선 확인
- [ ] 리팩터링 중 타입 에러를 일찍 발견한 사례 기록
- [ ] 개발자 피드백: 타입 검사가 도움이 된다는 응답이 50% 초과

## 참고

### 관련 BEP

- 없음(첫 타입 검사 개선 BEP)

### 외부 자료

- [MyPy Strict Mode Documentation](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
- [PEP 612 - Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [Gradual Typing Best Practices](https://mypy.readthedocs.io/en/stable/existing_code.html)

### 내부 문서

- 에러 분석 결과: `mypy_strict_check_all.txt`
- 에러 우선순위: `mypy_strict_priority.md`
- 구현 계획: `/Users/hyeokjin/.claude/plans/flickering-spinning-balloon.md`
