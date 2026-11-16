# 에이전트 아키텍처

## 요약

이 BEP(Backend.AI Enhancement Proposal)는 Backend.AI 에이전트의 커널 관리 아키텍처 개선안을 제시한다. 자원 관리가 일관되지 않고 상태 추적이 어려우며 pickle 기반 복구가 호환성 문제를 만드는 현재 문제를 풀기 위해 자원 중심의 새 아키텍처를 제안한다. 제안 아키텍처는 자원 lifecycle 관리를 구조화하고 상태 관리를 명확히 하며 에러 처리와 복구 수단을 강화하는 것을 목표로 한다.

## 동기

현재 에이전트는 컴포넌트마다 동작이 일관되지 않아 여러 문제를 겪는다. 첫째, 자원 생성과 정리가 서로 맞지 않는 경우가 많다. 커널로 container 를 관리하지만 일관된 정리가 보장되지 않는 경우가 있고, 커널과 container 의 1:1 대응이 빠지는 경우도 있다.

둘째, 재시도 로직을 위해 커널 정보를 **pickle** 로 저장한다. 이 때문에 하위 호환성 문제가 생겨 앞의 문제를 쉽게 수정할 수 없다.

마지막으로 상태를 모든 계층에서 저장하고 갱신할 수 있어 어디에서 어떤 값이 바뀌는지 추적하기 어렵다. 예를 들어 container 설정에 사용하는 환경 변수는 함수마다 갱신하고, 커널을 생성할 때 context 도 값으로 계속 갱신하며 마지막에 한 번 더 갱신한다. 그래서 context 안에서 함수마다 너무 많은 정보가 갱신되고, 문제가 생겼을 때 원인을 짚기 어렵다.

현재 문제를 개별적으로 수정하더라도 에이전트 아키텍처를 개선하지 않으면 문제가 모두 해결됐다고 확신할 수 없다. 그래서 에이전트 아키텍처를 개선해야 한다.

## 현재 구조

![커널 흐름](./1002/kernel-flow.png)

현재 커널 생성 흐름은 크게 다음 단계로 이뤄진다.

1.  커널 생성을 위한 **Context** 를 생성한다.
2.  이미지를 pull 한다.
3.  커널에 필요한 자원을 할당한다.
4.  container 설정 값을 생성한다.
5.  container 를 생성한다.
6.  container 와 커널 동작을 확인한다.

그러나 현재 커널 생성 흐름에는 다음 문제가 있다.

1.  **context** 가 커널 생성의 모든 상태를 관리한다.
      * 모든 상태를 context 안에서 관리하므로 문제가 생긴 곳을 추적하기 어렵다.
      * 서로 의존하는 동작을 모두 context 에서 관리해 코드를 변경하기 어렵다.
2.  커널 설정에 필요한 자원과 그 정리 코드가 서로 맞지 않는다.
      * container 생성은 생성 시점에 함수를 호출하지만, 정리 코드는 내부 event loop 에서 호출한다.
3.  에이전트가 커널 복구에 **pickle** 을 사용하므로 이전 버전과의 호환성 문제 때문에 새 버전을 수정하기 어렵다.
4.  에이전트와 커널 구조가 지나치게 한 덩어리라 동작을 이해하기 어렵다.
5.  커널 생성에 필요한 자원 의존 관계가 얽혀 있어 파악하기 어렵다.

## 제안 아키텍처

![에이전트 아키텍처](./1002/agent-architecture.png)

제안 아키텍처는 하나의 통합 계층인 에이전트가 모든 자원을 관리하는 대신, 관련 자원을 묶어 관리한다. 에이전트는 커널을 생성하고 생성된 커널을 관리하는 흐름만 맡는다.

생성된 커널마다 **kernel runner** 를 생성해 container 와 관련 자원을 관리한다. 커널을 종료해야 할 때 kernel runner 의 async task 를 종료하고 관련 자원을 모두 정리한다. 그래서 커널이 종료될 때 자원이 구조적으로 정리된다.

### 커널 생성

에이전트 안에서 자원을 관리하기 위해 자원 관리 클래스가 `AbstractResource` 를 상속한다. 할당할 자원은 커널이 생성될 때 커널에 등록한다. 커널이 종료되면 등록된 자원을 모두 해제한다. 그래서 커널 종료 시 자원이 구조적으로 정리된다.

커널의 자원 설정에 실패하면 커널을 종료하고 커널에 등록된 자원을 모두 해제한다.

### 커널 종료

커널을 종료해야 할 때 에이전트는 **kernel runner** 를 종료하고 kernel runner 에 등록된 자원을 모두 해제한다.

### 서버 정상 종료

에이전트가 종료 중이어도 사용자 container 는 계속 동작해야 한다. 이 경우 자원 회수 로직이 실행되지 않도록 kernel runner 를 취소한다.

이때 kernel runner 는 종료되지만 등록된 자원이 모두 해제되지는 않는다. 그러면 container 가 정리되지 않아 **dangling resource** 로 남을 수 있다. 이를 해결하기 위해 다음 에이전트가 시작할 때 이 dangling container 의 **label 정보** 를 사용해 Manager 에 **Dangling Container event** 를 보낸다. 에이전트는 로컬 상태만 알고 Backend.AI 전체 상태는 모르므로 Manager 에 Dangling Container event 를 보내고, Manager 는 Backend.AI 전체 재시작 로직에 따라 복구한다.

### 서버 비정상 종료

에이전트가 비정상 종료하면 kernel runner 를 종료할 수 없고, kernel runner 에 등록된 자원도 모두 해제되지 않는다. 정상 종료와 마찬가지로 이 경우에도 dangling container 의 label 정보를 사용해 Manager 에 **Dangling Container event** 를 보낸다.

### container 비정상 종료

container 가 비정상 종료하면 커널의 정상 동작을 보장할 수 없다. 이때 **Probing** 기능으로 커널이 정상 동작하는지 확인할 수 있다. 정상 동작하지 않으면 kernel runner 를 종료하고 등록된 자원을 모두 해제할 수 있다.

다만 이번 작업에서는 kernel runner 를 종료하지 않고 container 의 비정상 상태를 알리는 event 만 발생시킨다.

### 하위 호환성

![커널 event](./1002/kernel-event.png)

현재 에이전트 구조를 변경하면 하위 호환성 문제가 생길 수 있다.

1.  이전 버전에서 실행 중인 커널은 어떻게 복구하는가.
2.  이전 버전으로 롤백하면 새로 생성한 커널은 어떻게 복구하는가.

> 이전 버전에서 실행 중인 커널은 어떻게 복구하는가.

이 아키텍처에서 이전 버전의 커널을 복구하려면 container 에 저장된 **label 정보** 로 Manager 에 **Dangling Container event** 를 보낸다. 이 event 를 받은 Manager 는 실행 중인 기존 container 를 그대로 사용하는 **kernel wrapper** 를 생성해 커널을 복구한다. 이 방식으로 이전 버전에서 실행 중인 커널을 복구할 수 있고, 새 버전 커널도 같은 시나리오로 복구할 수 있다.

> 이전 버전으로 롤백하면 새로 생성한 커널은 어떻게 복구하는가.

현재 에이전트 구조는 커널 복구에 pickle 을 사용한다. 이전 버전으로 롤백하면 새 에이전트도 같은 방식으로 pickle 을 사용해야 한다. 이번 작업에서는 **flag** 로 에이전트와 Manager 모두에서 pickle 사용을 비활성화하는 구현을 추가해, 이 flag 를 활성화한 에이전트를 Manager 가 복구할 수 있게 한다. 안정성을 확보한 뒤 이전 버전에서 **breaking change** 를 도입해 pickle 을 사용하지 않는 구조로 옮긴다.

## 구현 계획

### 자원 관리

먼저 자원 관리를 위해 다음 인터페이스를 제안한다.

```python
class Provisioner(ABC, Generic[TSpec, TResource]):
    """
    Base class for all provisioners in the stage.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the provisioner.
        """
        raise NotImplementedError

    @abstractmethod
    async def setup(self, spec: TSpec) -> TResource:
        """
        Sets up the lifecycle stage.
        """
        raise NotImplementedError

    @abstractmethod
    async def teardown(self, resource: TResource) -> None:
        """
        Tears down the lifecycle stage.
        """
        raise NotImplementedError


class Stage(ABC, Generic[TSpec, TResource]):
    @abstractmethod
    def setup(self, spec_generator: SpecGenerator[TSpec]) -> None:
        """
        Sets up the lifecycle stage.
        """
        raise NotImplementedError

    @abstractmethod
    async def wait_for_resource(self) -> TResource:
        """
        Waits for the resource to be ready.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def teardown(self) -> None:
        """
        Tears down the lifecycle stage.
        """
        raise NotImplementedError
```

자원을 할당하는 `Provisioner` 와 자원을 관리하는 `Stage` 를 구현한다. 자원마다 의존성을 인자로 주입해 각 클래스 안의 상태 관리를 줄인다. 그래서 자원 의존 관계가 분명해지고 자원을 개별로 관리할 수 있다.

`Stage` 는 `Provisioner` 로 자원을 할당하고 자원이 준비될 때까지 기다린다. 자원마다 준비 시간과 dangling 상태에 대한 지표를 수집할 수 있고, 공통 처리는 `Stage` 안에서 맡을 수 있다.

#### 구현 예

```python

class ProvisionStage(Stage[TSpec, TResource]):
    """
    A stage that provisions a resource.

    This stage is used to provision a resource using a provisioner.
    It waits for the spec to be ready and then uses the provisioner to set up the resource.
    """
    _provisioner: Provisioner
    _resource: Optional[TResource]
    _setup_completed: asyncio.Event
    _prometheus: Any

    def __init__(self, provisioner: Provisioner):
        self._provisioner = provisioner
        self._resource = None
        self._setup_completed = asyncio.Event()
    
    async def setup(self, spec_generator: SpecGenerator[TSpec]) -> None:
        """
        Sets up the lifecycle stage.
        """
        spec = await spec_generator.wait_for_spec()
        try:
            resource = await self._provisioner.setup(spec)
            self._resource = resource
        except Exception as e:
            log.error("Failed to setup resource: %s", e)
        finally:
            self._setup_completed.set()
    
    async def wait_for_resource(self) -> TResource:
        await self._setup_completed.wait()
        if self._resource is None:
            raise RuntimeError("Resource setup failed")
        return self._resource

    async def teardown(self) -> None:
        """
        Tears down the lifecycle stage.
        """
        if self._resource is None:
            return
        await self._provisioner.teardown(self._resource)
        self._resource = None
```

### 자원 등록

커널 종료 시 자원을 구조적으로 정리하기 위해 다음 구조를 제안한다.

```python
class Runner:
    _resources: Sequence[AbstractResource]
    _closed_event: asyncio.Event

    def __init__(self, resources: Sequence[AbstractResource]):
        self._resources = resources
        self._closed_event = asyncio.Event()

    async def _setup(self) -> None:
        for resource in self._resources:
            try:
                await resource.setup()
            except Exception as e:
                raise

    async def _cleanup(self) -> None:
        for resource in self._resources:
            try:
                await resource.release()
            except Exception as e:
                ...

    async def start(self) -> None:
        """
        Start the runner.
        This will setup all resources and start runner loop.
        It will run until the runner is closed.
        """
        if self._closed_event.is_set():
            raise RuntimeError("Runner is already closed.")
        try:
            await self._setup()
        except Exception as e:
            await self._cleanup()
            raise
        asyncio.create_task(self._run())

    async def _run(self) -> None:
        try:
            await self._closed_event.wait()
        finally:
            await self._cleanup()

    async def close(self) -> None:
        """
        Close the runner.
        This will cleanup all resources.
        """
        self._closed_event.set()
```

`Runner` 는 자원을 lifecycle 에 따라 관리하는 클래스다. 이어서 event 를 발생시키는 observer 와 비정상 동작을 감지하는 probe 를 구현해 runner 에 붙여 runner 를 종료할 수 있다.

## 계획

이 아키텍처를 적용하려면 다음 단계를 거친다.

### 1단계: 현재 에이전트 테스트 코드 추가

기존 에이전트의 RPC 호출 서버 동작을 검사하는 테스트 코드를 작성한다. 이 단계로 기존 에이전트의 동작과 수정한 에이전트의 기대 동작이 같고 관련 부수 효과가 일관되게 동작함을 보장한다.

### 2단계: 새 에이전트 코드 추가

위에서 설명한 내용을 바탕으로 새 에이전트 코드를 작성한다. 다만 새로 작성한 에이전트 코드는 **feature flag** 로 활성화한다.

### 3단계: 기존 에이전트 코드 제거

충분히 테스트한 뒤 기존 에이전트 코드와 feature flag 를 제거해 새 에이전트 코드가 동작하게 한다.
