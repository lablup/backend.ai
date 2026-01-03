# Ruff Linter 설정 확장 계획

## 개요

현재 Backend.AI 프로젝트의 Ruff linter 설정을 확장하여 코드 품질을 향상시키는 계획입니다.

### 현재 설정

```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I"]
ignore = ["E203", "E731", "E501"]
```

### 목표

- 버그 패턴 조기 감지
- 코드 현대화 (Python 3.13 활용)
- 일관된 코드 스타일
- 성능 최적화 기회 발견

---

## Phase 1: 즉시 적용 (위반 0개)

### T10 (flake8-debugger)

**목적**: 디버거 코드가 프로덕션에 포함되는 것 방지

| 룰 | 감지 대상 |
|---|---|
| T100 | `import pdb` |
| T101 | `import ipdb` |
| T102 | `import pudb` |
| T103 | `breakpoint()` 호출 |

**예시**:
```python
# 감지됨 - 디버깅 코드 잔류
import pdb; pdb.set_trace()
breakpoint()
```

---

### FA (flake8-future-annotations)

**목적**: `from __future__ import annotations` 사용 권장

| 룰 | 설명 |
|---|---|
| FA100 | future annotations import 누락 시 타입 힌트에서 필요 |
| FA102 | future annotations 있을 때 불필요한 `__future__` import |

**효과**:
- 런타임 타입 평가 지연 (성능 향상)
- 순환 import 문제 해결 용이
- Forward reference 간소화

```python
# 권장
from __future__ import annotations

def foo() -> MyClass:  # 따옴표 없이 사용 가능
    ...
```

---

### ISC (flake8-implicit-str-concat)

**목적**: 암묵적 문자열 연결로 인한 버그 방지

| 룰 | 설명 |
|---|---|
| ISC001 | 같은 줄에서 암묵적 연결 |
| ISC002 | 여러 줄에서 암묵적 연결 |
| ISC003 | 명시적 연결 권장 |

**예시**:
```python
# 버그 가능성 - 쉼표 누락인지 의도인지 불명확
data = ["hello" "world"]  # ISC001

# 명확함
data = ["hello", "world"]
data = ["hello" + "world"]
```

---

### EXE (flake8-executable)

**목적**: 스크립트 파일의 shebang과 실행 권한 일관성

| 룰 | 설명 |
|---|---|
| EXE001 | shebang 있는데 실행 권한 없음 |
| EXE002 | 실행 권한 있는데 shebang 없음 |
| EXE003 | shebang에 공백 |
| EXE004 | shebang이 첫 줄이 아님 |

**예시**:
```bash
# 문제: shebang은 있는데 실행 불가
$ ls -la script.py
-rw-r--r-- script.py

$ head -1 script.py
#!/usr/bin/env python3

# 해결
$ chmod +x script.py
```

---

## Phase 2: 최소 수정 (10개 미만)

### LOG (flake8-logging) - 4개

**목적**: 로깅 모범 사례 적용

| 룰 | 설명 |
|---|---|
| LOG001 | `logging.getLogger()` 직접 호출 |
| LOG002 | 잘못된 로그 레벨 상수 |
| LOG007 | `logging.exception` 대신 `exc_info=True` |
| LOG009 | `warn()` 대신 `warning()` 사용 |

**예시**:
```python
# 나쁜 예
logging.warn("deprecated")

# 좋은 예
logging.warning("use this instead")
```

---

### FLY (flynt) - 8개

**목적**: 구식 문자열 포매팅을 f-string으로 변환

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| FLY002 | `.format()` 대신 f-string 사용 권장 | ✅ |

**예시**:
```python
# 변환 전
"Hello {}".format(name)
"Hello %s" % name

# 변환 후 (auto-fix)
f"Hello {name}"
```

---

## Phase 3: 소규모 수정 (50개 미만)

### PIE (flake8-pie) - 17개

**목적**: 불필요한 코드 패턴 제거

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| PIE794 | 중복 클래스 필드 정의 | ❌ |
| PIE796 | Enum 멤버에 불필요한 값 | ❌ |
| PIE807 | `lambda: []` 대신 `list` 사용 | ✅ |
| PIE810 | 중복 `startswith`/`endswith` | ✅ |

**예시**:
```python
# 변환 전
if s.startswith("a") or s.startswith("b"):
    ...

# 변환 후 (auto-fix)
if s.startswith(("a", "b")):
    ...
```

**ignore 권장**:
- `PIE790`: 불필요한 `pass` (가독성 위해 허용)

---

### FURB (refurb) - 34개

**목적**: 코드 현대화 및 관용적 표현 권장

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| FURB101 | `open().read()` 대신 `Path.read_text()` | ✅ |
| FURB103 | `open().write()` 대신 `Path.write_text()` | ✅ |
| FURB110 | `if x: return x` 패턴 단순화 | ✅ |
| FURB118 | `operator` 모듈 함수 활용 | ✅ |
| FURB129 | `readlines()` 대신 직접 반복 | ✅ |
| FURB140 | `itertools.starmap` 활용 | ✅ |
| FURB142 | `set().add()` 반복 대신 set comprehension | ✅ |

**예시**:
```python
# 변환 전
with open("file.txt") as f:
    content = f.read()

# 변환 후
content = Path("file.txt").read_text()
```

---

### DTZ (flake8-datetimez) - 42개

**목적**: timezone-aware datetime 사용 강제

| 룰 | 설명 |
|---|---|
| DTZ001 | `datetime.datetime()` 호출 시 `tzinfo` 없음 |
| DTZ002 | `datetime.today()` 대신 `datetime.now(tz=)` |
| DTZ003 | `datetime.utcnow()` deprecated |
| DTZ005 | `datetime.now()` 호출 시 `tz` 없음 |
| DTZ006 | `datetime.fromtimestamp()` 시 `tz` 없음 |
| DTZ007 | `datetime.strptime()` 결과에 timezone 없음 |

**예시**:
```python
# 나쁜 예 - naive datetime
now = datetime.now()
utc_now = datetime.utcnow()  # deprecated

# 좋은 예 - aware datetime
from datetime import UTC
now = datetime.now(tz=UTC)
```

---

## Phase 4: 중규모 수정 (100개 미만)

### T20 (flake8-print) - 71개 (CLI 제외 시)

**목적**: print문 대신 로깅 사용 권장

| 룰 | 설명 |
|---|---|
| T201 | `print()` 사용 감지 |
| T203 | `pprint()` 사용 감지 |

**per-file-ignores 설정**:
```toml
[tool.ruff.lint.per-file-ignores]
"src/ai/backend/*/cli/**/*.py" = ["T20"]
"src/ai/backend/cli/**/*.py" = ["T20"]
```

---

### RSE (flake8-raise) - 93개

**목적**: 올바른 예외 발생 패턴

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| RSE102 | 불필요한 괄호 `raise Exception()` → `raise Exception` | ✅ |

**예시**:
```python
# 인자 없을 때 괄호 불필요
raise ValueError()  # RSE102
raise ValueError    # OK

# 인자 있을 때는 괄호 필요
raise ValueError("message")  # OK
```

---

## Phase 5: 대규모 수정 (200개 미만)

### PERF (perflint) - 126개

**목적**: 성능 최적화 기회 발견

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| PERF101 | 불필요한 `list()` 감싸기 | ✅ |
| PERF102 | 불필요한 `dict.keys()`/`values()`/`items()` | ✅ |
| PERF203 | try-except 내 불필요한 코드 | ❌ |
| PERF401 | list comprehension 대신 `extend()` | ✅ |
| PERF402 | 불필요한 리스트 복사 | ✅ |
| PERF403 | dict comprehension 최적화 | ✅ |

**예시**:
```python
# 변환 전
for k in dict.keys():  # PERF102
    ...

# 변환 후
for k in dict:
    ...
```

---

### SIM (flake8-simplify) - 166개

**목적**: 코드 단순화

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| SIM101 | 중복 `isinstance()` 병합 | ✅ |
| SIM103 | 불필요한 `if-else` 반환 | ✅ |
| SIM110 | `any()`/`all()` 활용 | ✅ |
| SIM114 | 동일 분기 병합 | ✅ |
| SIM118 | `in dict.keys()` → `in dict` | ✅ |
| SIM300 | Yoda 조건문 수정 | ✅ |
| SIM401 | `dict.get()` 활용 | ✅ |

**예시**:
```python
# 변환 전
if key in dict.keys():  # SIM118
    ...
if "a" == x:  # SIM300 (Yoda)
    ...

# 변환 후
if key in dict:
if x == "a":
```

**ignore 권장**:
- `SIM102`: 중첩 if문 (가독성 위해 허용)
- `SIM105`: `contextlib.suppress` 강제 (명시적 except 선호)
- `SIM108`: 삼항연산자 강제 (가독성 저하)
- `SIM117`: 중첩 with문 (가독성 위해 허용)

---

### RUF (Ruff-specific) - 186개

**목적**: Ruff 고유 최적화 규칙

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| RUF005 | 비효율적 unpacking | ✅ |
| RUF006 | asyncio 태스크 저장 안 함 | ❌ |
| RUF010 | f-string 내 불필요한 `str()` | ✅ |
| RUF013 | 암묵적 Optional | ✅ |
| RUF015 | 불필요한 iterable 변환 | ✅ |
| RUF019 | 불필요한 key 함수 | ✅ |

**예시**:
```python
# 변환 전
[*a] + [*b]  # RUF005
f"{str(x)}"  # RUF010

# 변환 후
[*a, *b]
f"{x}"
```

**ignore 권장**:
- `RUF012`: mutable class attribute (ClassVar 강제)
- `RUF022`: `__all__` 정렬
- `RUF023`: `__slots__` 정렬
- `RUF100`: 불필요한 noqa

---

### C4 (flake8-comprehensions) - 197개

**목적**: 효율적인 comprehension 사용

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| C400 | `list()` 대신 list comprehension | ✅ |
| C401 | `set()` 대신 set comprehension | ✅ |
| C402 | `dict()` 대신 dict comprehension | ✅ |
| C403 | `set([...])` 대신 `{...}` | ✅ |
| C405 | `set([...])` 리터럴 대신 `{...}` | ✅ |
| C408 | `dict()` 대신 `{}` | ✅ |
| C416 | 불필요한 list comprehension | ✅ |
| C417 | 불필요한 `map()` | ✅ |

**예시**:
```python
# 변환 전
dict()  # C408
list(x for x in y)  # C400
[x for x in y]  # C416 (y가 이미 list면)

# 변환 후
{}
[x for x in y]
list(y)
```

---

## Phase 6: 검토 필요 (500개 이상)

### A (flake8-builtins) - 361개

**목적**: 빌트인 이름 섀도잉 방지

| 룰 | 설명 |
|---|---|
| A001 | 변수명이 빌트인과 충돌 |
| A002 | 함수 인자명이 빌트인과 충돌 |
| A003 | 클래스 속성명이 빌트인과 충돌 |

**흔한 위반**:
```python
# 빌트인 섀도잉
id = get_id()      # A001: id는 빌트인
type = "user"      # A001: type은 빌트인
list = [1, 2, 3]   # A001: list는 빌트인
input = get_input()  # A001: input은 빌트인

# 수정
user_id = get_id()
user_type = "user"
items = [1, 2, 3]
user_input = get_input()
```

---

### BLE (flake8-blind-except) - 455개

**목적**: 무분별한 예외 처리 방지

| 룰 | 설명 |
|---|---|
| BLE001 | bare `except:` 사용 금지 |

**예시**:
```python
# 나쁜 예 - 모든 예외 무시 (KeyboardInterrupt 포함)
try:
    ...
except:  # BLE001
    pass

# 좋은 예
try:
    ...
except Exception:
    pass
```

---

### RET (flake8-return) - 607개

**목적**: 일관된 return 스타일

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| RET501 | 불필요한 `return None` | ✅ |
| RET502 | 암묵적 return 후 명시적 `return None` | ✅ |
| RET503 | 암묵적/명시적 return 혼용 | ✅ |
| RET504 | return 전 불필요한 변수 할당 | ✅ |
| RET505 | `else` 후 `return` 불필요 | ✅ |
| RET506 | `else` 후 `raise` 불필요 | ✅ |

**예시**:
```python
# 변환 전
def foo():
    if condition:
        return True
    else:  # RET505: else 불필요
        return False

# 변환 후
def foo():
    if condition:
        return True
    return False
```

---

### B (flake8-bugbear) - 621개

**목적**: 일반적인 버그 패턴 감지

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| B006 | mutable 기본 인자 | ✅ |
| B007 | 미사용 loop 변수 | ✅ |
| B008 | 함수 호출을 기본 인자로 | ❌ |
| B009 | `getattr` 상수 키 | ✅ |
| B010 | `setattr` 상수 키 | ✅ |
| B017 | `pytest.raises(Exception)` | ❌ |
| B023 | loop 변수 클로저 바인딩 | ❌ |
| B024 | 추상 클래스에 추상 메서드 없음 | ❌ |
| B028 | `warnings.warn` stacklevel 누락 | ✅ |
| B904 | `raise ... from err` 누락 | ✅ |
| B905 | `zip()` strict 파라미터 권장 | ✅ |

**예시**:
```python
# B006: mutable 기본 인자
def foo(x=[]):  # 버그!
    x.append(1)
    return x

# 수정
def foo(x=None):
    if x is None:
        x = []
    x.append(1)
    return x

# B904: 예외 체이닝
try:
    ...
except ValueError as e:
    raise RuntimeError("failed") from e  # from e 추가
```

---

### ANN (flake8-annotations) - 1,261개+

**목적**: 타입 어노테이션 강제

| 룰 | 설명 |
|---|---|
| ANN001 | 함수 인자 타입 누락 |
| ANN002 | `*args` 타입 누락 |
| ANN003 | `**kwargs` 타입 누락 |
| ANN201 | public 함수 리턴 타입 누락 |
| ANN202 | private 함수 리턴 타입 누락 |
| ANN204 | special method 리턴 타입 누락 |
| ANN205 | static method 리턴 타입 누락 |
| ANN206 | class method 리턴 타입 누락 |
| ANN401 | `Any` 타입 사용 |

**예시**:
```python
# ANN201: 리턴 타입 누락
def add(a: int, b: int):  # -> int 누락
    return a + b

# 수정
def add(a: int, b: int) -> int:
    return a + b
```

**ignore 권장**:
- `ANN204`: special method (`__init__` 등) - 보통 `-> None`
- `ANN401`: `Any` 타입 - mypy에서 이미 검사

---

### UP (pyupgrade) - 2,000개

**목적**: Python 최신 문법 활용

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| UP006 | `List[str]` → `list[str]` | ✅ |
| UP007 | `Optional[X]` → `X \| None` | ✅ |
| UP035 | 불필요한 `typing` import | ✅ |
| UP043 | 불필요한 `None` 기본값 | ✅ |

**예시**:
```python
# 변환 전
from typing import List, Optional

def foo(x: Optional[List[str]] = None) -> List[str]:
    ...

# 변환 후
def foo(x: list[str] | None = None) -> list[str]:
    ...
```

**ignore 권장**:
- `UP007`: `Optional[X]` 스타일 유지 (선택적)
- `UP040`: TypeAlias → type statement
- `UP045`, `UP046`, `UP047`: TypeVar/Generic 관련 (대규모 변경)

---

### TID252 (flake8-tidy-imports) - 2,392개

**목적**: 부모 모듈 상대 import 금지

| 룰 | 설명 | auto-fix |
|---|---|:---:|
| TID252 | `from ..` 상대 import → 절대 import | ✅ |

**예시**:
```python
# 변환 전
from ..common import utils
from ...models import User

# 변환 후
from ai.backend.common import utils
from ai.backend.models import User
```

---

## 설정 템플릿

### 최종 권장 설정

```toml
[tool.ruff]
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = [
    # 기본 (현재)
    "E",        # pycodestyle errors
    "W",        # pycodestyle warnings
    "F",        # pyflakes
    "I",        # isort

    # Phase 1: 즉시 적용
    "T10",      # flake8-debugger
    "FA",       # flake8-future-annotations
    "ISC",      # flake8-implicit-str-concat
    "EXE",      # flake8-executable

    # Phase 2-3: 최소 수정
    "LOG",      # flake8-logging
    "FLY",      # flynt
    "PIE",      # flake8-pie
    "FURB",     # refurb
    "DTZ",      # flake8-datetimez

    # Phase 4: 중규모 수정
    "T20",      # flake8-print
    "RSE",      # flake8-raise

    # Phase 5: 대규모 수정
    "PERF",     # perflint
    "SIM",      # flake8-simplify
    "RUF",      # Ruff-specific
    "C4",       # flake8-comprehensions

    # Phase 6: 검토 필요
    "A",        # flake8-builtins
    "BLE",      # flake8-blind-except
    "RET",      # flake8-return
    "B",        # flake8-bugbear
    "ANN",      # flake8-annotations
    "UP",       # pyupgrade
    "TID252",   # relative imports
]

ignore = [
    # 기본 유지
    "E203",     # 슬라이스 공백 (formatter 충돌)
    "E731",     # lambda 대입 허용
    "E501",     # 줄 길이 (formatter 처리)

    # SIM: 가독성 유지
    "SIM102",   # 중첩 if문 허용
    "SIM105",   # contextlib.suppress 강제 안함
    "SIM108",   # 삼항연산자 강제 안함
    "SIM117",   # 중첩 with문 허용

    # RUF: 불필요한 변경 방지
    "RUF012",   # mutable class attribute
    "RUF022",   # __all__ 정렬
    "RUF023",   # __slots__ 정렬
    "RUF100",   # 불필요한 noqa

    # PIE
    "PIE790",   # 불필요한 pass 허용

    # UP: 기존 스타일 유지
    "UP007",    # Optional[X] 스타일 유지 (선택)
    "UP040",    # TypeAlias 유지
    "UP045",    # TypeVar 유지
    "UP046",    # Generic 유지
    "UP047",    # Generic 함수 유지

    # ANN
    "ANN204",   # special method 리턴 타입
    "ANN401",   # Any 타입 허용
]

[tool.ruff.lint.per-file-ignores]
"src/ai/backend/manager/config.py" = ["E402"]
"src/ai/backend/manager/models/alembic/env.py" = ["E402"]
# CLI는 print 허용
"src/ai/backend/*/cli/**/*.py" = ["T20"]
"src/ai/backend/cli/**/*.py" = ["T20"]

[tool.ruff.lint.isort]
known-first-party = ["ai.backend"]
known-local-folder = ["src"]
known-third-party = ["alembic", "redis", "kubernetes"]
split-on-trailing-comma = true
```

---

## 적용 체크리스트

### Phase 1 (즉시)
- [ ] T10, FA, ISC, EXE 추가
- [ ] `pants lint ::` 확인

### Phase 2-3 (최소 수정)
- [ ] LOG 추가 → fix 실행
- [ ] FLY 추가 → fix 실행
- [ ] PIE 추가 (PIE790 ignore) → fix 실행
- [ ] FURB 추가 → fix 실행
- [ ] DTZ 추가 → 수동 수정 필요

### Phase 4 (중규모)
- [ ] T20 추가 + per-file-ignores 설정
- [ ] RSE 추가 → fix 실행

### Phase 5 (대규모)
- [ ] PERF 추가 → fix 실행
- [ ] SIM 추가 (102,105,108,117 ignore) → fix 실행
- [ ] RUF 추가 (012,022,023,100 ignore) → fix 실행
- [ ] C4 추가 → fix 실행

### Phase 6 (검토 필요)
- [ ] A 추가 → 변수명 검토 필요
- [ ] BLE 추가 → except 블록 검토
- [ ] RET 추가 → fix 실행
- [ ] B 추가 → 버그 패턴 수정
- [ ] ANN 추가 (204, 401 ignore) → 타입 추가
- [ ] UP 추가 (007,040,045-047 ignore) → fix 실행
- [ ] TID252 추가 → fix 실행

---

## 참고 자료

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
