# 제목

## 관련 이슈

- JIRA: BA-XXXX
- GitHub: #XXXX

## 동기

이 변경이 필요한 이유와 해결하려는 문제를 적는다.

예시:
> 현재 `StringFilter` 는 정의된 filter field 10개 중 4개만 지원한다.
> 사용자는 모든 filter field 가 동작하기를 기대하지만 `starts_with`, `ends_with`, `not_equals` 는 조용히 무시된다.
> 그래서 혼란이 생기고 질의 결과를 예상할 수 없다.

## 현재 설계

이 제안이 바꾸려는 현재 상태나 설계를 설명한다.

예시:
> ```python
> def build_query_condition(
>     self,
>     contains_factory: Callable[[str, bool], QueryCondition],
>     equals_factory: Callable[[str, bool], QueryCondition],
> ) -> Optional[QueryCondition]:
>     # Only 4 fields are handled, others are ignored
> ```

## 제안 설계

새로 제안하는 설계나 변경 사항을 설명한다.

예시:
> ```python
> @dataclass
> class StringMatchSpec:
>     value: str
>     case_insensitive: bool = False
>     negated: bool = False
>
> def build_query_condition(
>     self,
>     contains_factory: Callable[[StringMatchSpec], QueryCondition],
>     equals_factory: Callable[[StringMatchSpec], QueryCondition],
>     starts_with_factory: Callable[[StringMatchSpec], QueryCondition],
>     ends_with_factory: Callable[[StringMatchSpec], QueryCondition],
> ) -> Optional[QueryCondition]:
>     # All fields are now handled
> ```

## 이전 / 호환성

뒤 호환성 고려 사항과 이전 계획을 해당하면 설명한다.

예시:
> ### 하위 호환성
> - 기존 `build_query_condition()` 호출은 수정이 필요하다
> - 새 factory 파라미터는 필수다 (기본값 없음)
>
> ### 호환성을 깨는 변경
> - factory 시그니처가 `Callable[[str, bool], QueryCondition]` 에서 `Callable[[StringMatchSpec], QueryCondition]` 로 변경된다
>
> ### 이전 단계
> 1. 모든 adapter 구현을 새 `StringMatchSpec` 을 쓰도록 수정한다
> 2. 모든 호출부에 `starts_with_factory` 와 `ends_with_factory` 를 추가한다
> 3. 모든 filter 조합을 테스트한다

## 구현 계획

구현 단계와 우선순위를 정리한다.

예시:
> 1. **1단계**: 핵심 변경
>    - `StringMatchSpec` dataclass 추가
>    - `StringFilter.build_query_condition()` 시그니처 수정
>
> 2. **2단계**: adapter 수정
>    - `ScalingGroupFilterGQL` adapter 수정
>    - `StringFilter` 를 사용하는 다른 adapter 수정
>
> 3. **3단계**: 테스트
>    - 모든 filter field 조합에 대한 unit test 추가
>    - GraphQL 질의에 대한 integration test 추가

## 열린 질문

해결되지 않은 질문이나 더 논의할 항목을 나열한다.

예시:
> - `StringFilter` 에 `not_contains`, `not_starts_with`, `not_ends_with` field 추가
> - 하위 호환성을 위한 factory 파라미터의 기본값 `None` 선택 항목 여부

## 참고

- 관련 문서, 논의, 외부 자료 링크

예시:
> - [BEP-1010: New GQL](BEP-1010-new-gql.md)
> - [Strawberry GraphQL 문서](https://strawberry.rocks/)
