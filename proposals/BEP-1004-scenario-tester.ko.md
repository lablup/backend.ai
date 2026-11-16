# 에이전트 아키텍처

## 요약

Backend.AI Tester 는 실제 사용자 시나리오를 자동화해 시스템의 여러 기능과 동작을 독립적으로 검증하는 컴포넌트다. 기존 단위 테스트, 통합 테스트와 달리 장시간 실행되는 세션, 자원 정리, 컴포넌트 사이의 복잡한 상호작용처럼 실제 환경에서 생길 수 있는 문제를 시뮬레이션해 검증한다. Tester 는 별도 서비스로 동작하며 다양한 테스트 케이스와 시나리오를 정의하고 실행하며 결과를 체계적으로 기록하고 보고해 Backend.AI 의 신뢰성과 유지보수성을 크게 높인다.

## 동기

Backend.AI 의 규모와 기능이 커지면서 시스템 복잡도가 높아져 유지보수와 검증이 더 어려워졌다. 이를 해결하기 위해 Tester 라는 새 컴포넌트를 도입한다. Tester 는 Backend.AI 의 여러 기능을 테스트하고 시스템 동작을 검증해 안정성과 신뢰성을 높이며, 개발자가 시스템을 더 잘 이해하고 유지보수하도록 돕는다.

지금도 단위 테스트와 통합 테스트를 사용하지만 실제 운영을 검증하기에는 부족하다. 예를 들어 장시간 실행되는 세션이 올바르게 동작하는지, 여러 작업 뒤에 자원이 제대로 정리되는지, 컴포넌트가 기대대로 상호작용하는지 확인하려면 사용자 동작을 시뮬레이션해 검증해야 한다. Tester 는 이런 시나리오를 자동으로 실행하고 결과를 검증하는 기능을 제공해 시스템이 올바르게 동작하도록 보장한다.

## Tester

![Tester](./1004/tester-basic.svg)

Tester 는 Backend.AI 서비스와 분리된 컴포넌트로, Backend.AI API 를 호출해 동작을 검증한다. 그래서 Backend.AI 의 동작을 독립적으로 테스트할 수 있다. Tester 는 다양한 테스트 케이스를 정의하고 실행하며 결과를 검증한다.

Tester 는 다음 컴포넌트로 이뤄진다.

## Tester 아키텍처

![테스트 시나리오](./1004/tester-architecture.png)

Tester 는 세 가지 주요 컴포넌트로 구성된다.

1. **Test Spec**: 테스트 시나리오를 정의한다. 각 테스트 케이스는 특정 동작을 지정하고 결과를 검증한다. test spec 은 시나리오 이름을 Tester 가 수행하는 동작에 대응시켜 특정 시나리오나 그룹을 실행할 수 있게 한다.

2. **Test Runner**: test spec 을 실행한다. spec 에 정의된 동작을 순서대로 수행하고 결과를 검증한다. runner 는 spec 을 읽고 각 동작을 수행하며 결과를 기록하고, 기록은 exporter 를 통해 외부 보고나 로그로 전달된다.

3. **Test Case**: 개별 테스트 케이스를 정의한다. 각 케이스는 동작을 지정하고 결과를 검증한다. 테스트 케이스는 spec 에 정의된 동작을 수행하고 결과를 검증해 시스템 동작을 확인한다.

### Test Suite

test spec 에 테스트 케이스를 여럿 담을 수 있어 다양한 시나리오를 정의할 수 있다. 각 테스트 케이스는 동작을 지정하고 결과를 검증한다. test spec 은 케이스를 묶어 특정 시나리오를 수행한다.

테스트 케이스의 일부 동작은 반복될 수 있다. 예를 들어 세션 테스트는 세션을 생성하고 조작하고 종료하는 일을 반복할 수 있다. 이를 지원하려고 Test Suite 개념을 도입한다.

![Test Suite](./1004/test-suite.png)

1. **Sequence Test Suite**: 테스트 케이스를 순서대로 실행한다. 각 케이스는 앞선 결과를 바탕으로 실행된다. 단계가 실패하면 뒤 테스트를 건너뛰고 실패 정보를 기록한다.

2. **Wrapper Test Suite**: 테스트 케이스의 setup 과 teardown 동작을 정의한다. 각 케이스는 정의된 대로 setup 과 teardown 을 수행해 완료 뒤 자원이 제대로 정리되도록 보장한다.

## Test Spec 예

```python
class TestTag(enum.StrEnum):
    # component based tags
    MANAGER = "manager"
    AGENT = "agent"

    # Domain specific tags
    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"

@dataclass
class TestSpec:
    name: str
    description: str
    tags: set[TestTag]
    test_case: TestCase


class TestSpecManager:
    
    _specs: set[TestSpec]

    def __init__(self, specs: set[TestSpec]) -> None:
        self._specs = specs
    
    def all_specs(self) -> set[TestSpec]:
        """
        Get all test specifications.
        """
        return self._specs
    
    def specs_by_tag(self, tag: TestTag) -> set[TestSpec]:
        """
        Get test specifications by tag.
        """
        return {spec for spec in self._specs if tag in spec.tags}

    def specs_by_name(self, name: str) -> set[TestSpec]:
        """
        Get test specifications by name.
        """
        return {spec for spec in self._specs if spec.name == name}
```

TestSpec 과 TestSpecManager 는 위와 같이 구현한다. TestSpecManager 는 모든 test spec 을 관리하고 tag 나 name 으로 조회하는 함수를 제공한다. 사용자는 TestSpecManager 로 원하는 spec 을 조회하고 실행할 수 있다.

## Tester Runner 예

```python
class TestExporter(ABC):
    async def export_done(self, spec: TestSpec) -> None:
        """
        Export the result of a test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def export_exception(self, spec: TestSpec, exception: BaseException) -> None:
        """
        Export the exception that occurred during the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    

class TestRunner:
    _spec: TestSpec
    _exporter: TestExporter

    def __init__(self, spec: TestSpec, exporter: TestExporter) -> None:
        self._spec = spec
        self._exporter = exporter
    
    async def run(self) -> None:
        try:
            await self._spec.test_case.run_test()
            await self._exporter.export_done(self._spec)
        except BaseException as e:
            await self._exporter.export_exception(self._spec, e)

_DEFAULT_CONCURRENCY = 10

class Tester:
    _spec_manager: TestSpecManager
    _exporter: TestExporter
    _semaphore: asyncio.Semaphore

    def __init__(self, spec_manager: TestSpecManager, exporter: TestExporter) -> None:
        self._spec_manager = spec_manager
        self._exporter = exporter
        self._semaphore = asyncio.Semaphore(_DEFAULT_CONCURRENCY)
    
    async def _run_spec(self, spec: TestSpec) -> None:
        """
        Run a single test specification.
        """
        async with self._semaphore:
            print(f"Running test: {spec.name}")
            runner = TestRunner(spec, self._exporter)
            await runner.run()
            print(f"Finished test: {spec.name}")
        
    async def run_all(self) -> None:
        """
        Run all test specifications.
        """
        for spec in self._spec_manager.all_specs():
            asyncio.create_task(self._run_spec(spec))

    async def run_by_tag(self, tag: TestTag) -> None:
        """
        Run test specifications by tag.
        """
        for spec in self._spec_manager.specs_by_tag(tag):
            asyncio.create_task(self._run_spec(spec))

        
    async def run_by_name(self, name: str) -> None:
        """
        Run test specifications by name.
        """
        for spec in self._spec_manager.specs_by_name(name):
            asyncio.create_task(self._run_spec(spec))
```

TestRunner 와 Tester 는 위와 같이 구현한다. TestRunner 는 test spec 하나를 실행하고 exporter 로 결과를 전달한다. Tester 는 동시 실행 수를 제한해 여러 spec 을 실행하고 결과를 효율적으로 기록한다.
