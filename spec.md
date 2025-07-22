# Background
src/ai/backend/manager/actions 아래의 action과 processor를 액션 타입에 따라 재정의하는 리팩토링을 진행하였다.
기존 BaseAction은 single_entity 아래의 BaseSingleEntityAction으로, BaseBatchAction은 BaseMultiEntityAction으로 바뀌었고 BaseScopeAction을 추가하였다.
Processor또한 single entity와 multi entity에 따라 분리하고 Scope action을 처리하는 processor를 추가했다.

# TODO
기존 BaseAction과 Processor를 사용하는 코드에 모두 업데이트가 필요하다.
import문과 변수명에 주로 업데이트가 필요할 것이다.

# Goal
`pants check ::` 커맨드를 실행하여 타입 체크에 문제가 발생하지 않아야 한다.

# Other instructions
- BaseScopeAction은 아직 구현된 곳이 없으니 다른 모듈에서 import 하지 말 것
- 테스트 코드는 지금 추가하지 말 것
- src/ai/backend/manager/actions 외부의 모듈에서 `ai.backend.manager.actions.action.base.BaseAction`를 절대 상속받지 말 것