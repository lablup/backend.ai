# GQL StringFilter 확장

## 관련 이슈

- JIRA: BA-3640

## 동기

`StringFilter` GraphQL input type 은 문자열 일치 연산을 빠짐없이 제공해야 한다.

| 연산 | 기본 | 대소문자 무시 | NOT | 대소문자 무시 NOT |
|-----------|-------|------------------|-----|---------------------|
| equals | `equals` | `iEquals` | `notEquals` | `iNotEquals` |
| contains | `contains` | `iContains` | `notContains` | `iNotContains` |
| starts_with | `startsWith` | `iStartsWith` | `notStartsWith` | `iNotStartsWith` |
| ends_with | `endsWith` | `iEndsWith` | `notEndsWith` | `iNotEndsWith` |

**총 16개 filter field**

그런데 이전 `build_query_condition()` method 는 이 중 **4개 field 만** 구현했다.
- `equals`, `iEquals`
- `contains`, `iContains`

나머지 field 는 아무 에러나 경고 없이 무시되어 혼란과 예상하지 못한 동작을 일으켰다.

## 현재 설계 (확장 이전)

```python
@strawberry.input
class StringFilter:
    contains: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    equals: Optional[str] = None
    not_equals: Optional[str] = None

    i_contains: Optional[str] = strawberry.field(name="iContains", default=None)
    i_starts_with: Optional[str] = strawberry.field(name="iStartsWith", default=None)
    i_ends_with: Optional[str] = strawberry.field(name="iEndsWith", default=None)
    i_equals: Optional[str] = strawberry.field(name="iEquals", default=None)
    i_not_equals: Optional[str] = strawberry.field(name="iNotEquals", default=None)

    def build_query_condition(
        self,
        contains_factory: Callable[[str, bool], QueryCondition],
        equals_factory: Callable[[str, bool], QueryCondition],
    ) -> Optional[QueryCondition]:
        # Only 4 fields are handled, others are silently ignored
        if self.equals:
            return equals_factory(self.equals, False)
        if self.i_equals:
            return equals_factory(self.i_equals, True)
        if self.contains:
            return contains_factory(self.contains, False)
        if self.i_contains:
            return contains_factory(self.i_contains, True)
        return None
```

### 문제

1. **실패를 알리지 않음**: 대부분 filter field 가 아무 에러나 경고 없이 무시된다
2. **불완전한 API**: 사용자가 `starts_with`, `ends_with`, 부정 연산을 사용할 수 없다
3. **NOT variant 부재**: `not_contains`, `not_starts_with`, `not_ends_with` field 가 없다
4. **factory signature 제약**: 현재 factory signature 인 `Callable[[str, bool], QueryCondition]` 로는 부정을 표현할 수 없다

## 제안 설계

### StringMatchSpec dataclass

일치 조건을 담는 dataclass 를 도입한다.

```python
@dataclass(frozen=True)
class StringMatchSpec:
    """Specification for string matching operations."""
    value: str
    case_insensitive: bool
    negated: bool
```

모든 field 는 기본값 없이 필수로 두어 일치 동작을 명시적으로 지정하게 한다.

### 변경된 factory signature

factory parameter 가 `StringMatchSpec` 을 사용하도록 변경한다.

```python
def build_query_condition(
    self,
    contains_factory: Callable[[StringMatchSpec], QueryCondition],
    equals_factory: Callable[[StringMatchSpec], QueryCondition],
    starts_with_factory: Callable[[StringMatchSpec], QueryCondition],
    ends_with_factory: Callable[[StringMatchSpec], QueryCondition],
) -> Optional[QueryCondition]:
    """Build a query condition from this filter using the provided factory callables.

    Args:
        contains_factory: Factory for LIKE '%value%' operations
        equals_factory: Factory for exact match (=) operations
        starts_with_factory: Factory for LIKE 'value%' operations
        ends_with_factory: Factory for LIKE '%value' operations

    Returns:
        QueryCondition if any filter field is set, None otherwise
    """
    # equals operations
    if self.equals:
        return equals_factory(
            StringMatchSpec(self.equals, case_insensitive=False, negated=False)
        )
    if self.i_equals:
        return equals_factory(
            StringMatchSpec(self.i_equals, case_insensitive=True, negated=False)
        )
    if self.not_equals:
        return equals_factory(
            StringMatchSpec(self.not_equals, case_insensitive=False, negated=True)
        )
    if self.i_not_equals:
        return equals_factory(
            StringMatchSpec(self.i_not_equals, case_insensitive=True, negated=True)
        )

    # contains operations
    if self.contains:
        return contains_factory(
            StringMatchSpec(self.contains, case_insensitive=False, negated=False)
        )
    if self.i_contains:
        return contains_factory(
            StringMatchSpec(self.i_contains, case_insensitive=True, negated=False)
        )
    if self.not_contains:
        return contains_factory(
            StringMatchSpec(self.not_contains, case_insensitive=False, negated=True)
        )
    if self.i_not_contains:
        return contains_factory(
            StringMatchSpec(self.i_not_contains, case_insensitive=True, negated=True)
        )

    # starts_with operations
    if self.starts_with:
        return starts_with_factory(
            StringMatchSpec(self.starts_with, case_insensitive=False, negated=False)
        )
    if self.i_starts_with:
        return starts_with_factory(
            StringMatchSpec(self.i_starts_with, case_insensitive=True, negated=False)
        )
    if self.not_starts_with:
        return starts_with_factory(
            StringMatchSpec(self.not_starts_with, case_insensitive=False, negated=True)
        )
    if self.i_not_starts_with:
        return starts_with_factory(
            StringMatchSpec(self.i_not_starts_with, case_insensitive=True, negated=True)
        )

    # ends_with operations
    if self.ends_with:
        return ends_with_factory(
            StringMatchSpec(self.ends_with, case_insensitive=False, negated=False)
        )
    if self.i_ends_with:
        return ends_with_factory(
            StringMatchSpec(self.i_ends_with, case_insensitive=True, negated=False)
        )
    if self.not_ends_with:
        return ends_with_factory(
            StringMatchSpec(self.not_ends_with, case_insensitive=False, negated=True)
        )
    if self.i_not_ends_with:
        return ends_with_factory(
            StringMatchSpec(self.i_not_ends_with, case_insensitive=True, negated=True)
        )

    return None
```

### adapter 구현 예시

```python
class ScalingGroupFilterAdapter:
    @staticmethod
    def build_name_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            column = sa.func.lower(column)
            value = spec.value.lower()
        else:
            value = spec.value

        condition = column == value
        if spec.negated:
            condition = sa.not_(condition)
        return condition

    @staticmethod
    def build_name_contains_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            condition = column.ilike(f"%{spec.value}%")
        else:
            condition = column.like(f"%{spec.value}%")

        if spec.negated:
            condition = sa.not_(condition)
        return condition

    @staticmethod
    def build_name_starts_with_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            condition = column.ilike(f"{spec.value}%")
        else:
            condition = column.like(f"{spec.value}%")

        if spec.negated:
            condition = sa.not_(condition)
        return condition

    @staticmethod
    def build_name_ends_with_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            condition = column.ilike(f"%{spec.value}")
        else:
            condition = column.like(f"%{spec.value}")

        if spec.negated:
            condition = sa.not_(condition)
        return condition
```

## 이전 / 호환성

### 호환성을 깨는 변경

1. **factory signature 변경**: `Callable[[str, bool], QueryCondition]` → `Callable[[StringMatchSpec], QueryCondition]`
2. **필수 parameter 추가**: `starts_with_factory` 와 `ends_with_factory` 가 필수가 된다

### 하위 호환성

- 기존 filter field 는 모두 같은 GraphQL 이름으로 계속 사용할 수 있다
- GraphQL schema 와 client 에 노출되는 API 는 변경하지 않는다

### 이전 단계

1. `ai.backend.manager.api.gql.base` 에 `StringMatchSpec` dataclass 를 추가한다
2. `StringFilter.build_query_condition()` 의 signature 를 변경한다
3. `build_query_condition()` 을 사용하는 adapter 구현을 모두 변경한다
4. filter field 조합마다 unit test 를 추가한다

## 구현 계획

### Phase 1: 핵심 변경
- `StringMatchSpec` dataclass 추가
- `StringFilter.build_query_condition()` method 의 signature 와 구현 변경

### Phase 2: adapter 변경
- `ScalingGroupFilterGQL` adapter 변경
- `StringFilter` 를 사용하는 다른 adapter 변경 (codebase 에서 사용처 검색)

### Phase 3: 테스트
- 16개 filter field 마다 unit test 추가
- 부정 연산 unit test 추가
- GraphQL query integration test 추가

## 설계 결정

### NOT variant 전부 제공

부정을 빠짐없이 다루려고 NOT variant 인 not_contains, i_not_contains, not_starts_with, i_not_starts_with, not_ends_with, i_not_ends_with 를 모두 추가하기로 했다.

- **일관성**: 4개 연산(equals, contains, starts_with, ends_with)이 이제 같은 4가지 variant(기본, 대소문자 무시, NOT, 대소문자 무시 NOT)을 가진다
- **API 완전성**: 사용자가 우회 없이 어떤 문자열 일치 조합이든 실행할 수 있다
- **향후 확장**: 나중에 field 를 더 추가할 필요가 없다

### StringMatchSpec 에 기본값을 두지 않음

`StringMatchSpec` 은 모든 field 를 명시적으로 요구한다.
- `value: str` - 검색할 값
- `case_insensitive: bool` - 대소문자 무시 여부
- `negated: bool` - 조건 부정 여부

이 설계는 호출하는 코드가 일치 동작을 모두 명시하게 하여 잘못된 기본값에서 비롯된 버그를 줄인다.

## 참고

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [Strawberry GraphQL 문서](https://strawberry.rocks/)
