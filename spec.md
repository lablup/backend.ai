근# 스케줄러 리팩토링 설계 명세서

## 개요

현재 `SchedulerDispatcher`의 스케줄링 프로세스는 여러 단계로 구성되어 있으며, 각 단계가 명확히 분리되어야 한다. 단일 `schedule()` 메서드로는 이 복잡성을 표현하기 어려우므로, 더 세분화된 인터페이스를 설계한다.

## 현재 스케줄링 프로세스 분석

### 스케줄링 플로우
1. **세션 선택** (Pick): 대기 중인 세션 중 하나를 선택
2. **사전 조건 검사** (Validate): 선택된 세션의 스케줄링 가능 여부 검증
3. **리소스 매칭** (Match): 적합한 에이전트 찾기
4. **리소스 할당** (Allocate): 실제 리소스 예약 및 할당
5. **상태 전이** (Finalize): 세션 상태 업데이트 및 이벤트 발생

### 각 단계의 특성
- **Pick**: 우선순위, 정책에 따른 선택 로직
- **Validate**: 다양한 제약 조건 검증 (predicates)
- **Match**: 리소스 요구사항과 가용 리소스 매칭
- **Allocate**: 트랜잭션 처리, 동시성 제어 필요
- **Finalize**: 상태 업데이트, 이벤트 발생

## 세분화된 인터페이스 설계

### 1. 핵심 인터페이스들

```python
from typing import Protocol, Optional, TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')  # 스케줄링 대상 타입

# 1. 선택 인터페이스
class ISelector(ABC, Generic[T]):
    """스케줄링 대상을 선택하는 인터페이스"""
    
    @abstractmethod
    async def select(
        self,
        candidates: list[T],
        context: SelectionContext,
    ) -> Optional[T]:
        """후보 중에서 하나를 선택"""
        pass

# 2. 검증 인터페이스
class IValidator(ABC, Generic[T]):
    """스케줄링 가능 여부를 검증하는 인터페이스"""
    
    @abstractmethod
    async def validate(
        self,
        target: T,
        context: ValidationContext,
    ) -> ValidationResult:
        """대상의 스케줄링 가능 여부 검증"""
        pass

# 3. 매칭 인터페이스
class IMatcher(ABC, Generic[T]):
    """리소스 요구사항과 가용 리소스를 매칭하는 인터페이스"""
    
    @abstractmethod
    async def match(
        self,
        target: T,
        resources: list[ResourceInfo],
        context: MatchingContext,
    ) -> Optional[ResourceMatch]:
        """적합한 리소스 찾기"""
        pass

# 4. 할당 인터페이스
class IAllocator(ABC):
    """리소스를 실제로 할당하는 인터페이스"""
    
    @abstractmethod
    async def allocate(
        self,
        match: ResourceMatch,
        context: AllocationContext,
    ) -> AllocationResult:
        """리소스 할당 및 예약"""
        pass

# 5. 완료 처리 인터페이스
class IFinalizer(ABC, Generic[T]):
    """스케줄링 완료 후 처리를 담당하는 인터페이스"""
    
    @abstractmethod
    async def finalize(
        self,
        target: T,
        allocation: AllocationResult,
        context: FinalizationContext,
    ) -> None:
        """상태 업데이트 및 이벤트 발생"""
        pass
```

### 2. 컨텍스트 및 결과 타입

```python
@dataclass
class SelectionContext:
    """선택 단계에서 필요한 컨텍스트"""
    total_capacity: ResourceSlot
    existing_sessions: list[SessionRow]
    scheduler_config: dict[str, Any]

@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    failed_checks: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)

@dataclass
class ResourceMatch:
    """매칭 결과"""
    target: Any  # 스케줄링 대상
    resource: Any  # 매칭된 리소스
    allocation_plan: dict[str, Any]  # 할당 계획

@dataclass
class AllocationResult:
    """할당 결과"""
    success: bool
    allocated_resources: Optional[dict[str, Any]]
    error: Optional[str]
```

### 3. 구체적인 구현 예시

```python
# 세션 선택기
class SessionSelector(ISelector[SessionRow]):
    """기존 AbstractScheduler를 활용한 세션 선택"""
    
    def __init__(self, strategy: AbstractScheduler):
        self.strategy = strategy
    
    async def select(
        self,
        candidates: list[SessionRow],
        context: SelectionContext,
    ) -> Optional[SessionRow]:
        # 우선순위별로 필터링
        priority, filtered = self.strategy.prioritize(candidates)
        
        # 세션 선택
        session_id = self.strategy.pick_session(
            context.total_capacity,
            filtered,
            context.existing_sessions
        )
        
        if session_id:
            return next(s for s in candidates if s.id == session_id)
        return None

# 세션 검증기
class SessionValidator(IValidator[SessionRow]):
    """Predicate 체크를 수행하는 검증기"""
    
    def __init__(self, predicates: list[PredicateChecker]):
        self.predicates = predicates
    
    async def validate(
        self,
        target: SessionRow,
        context: ValidationContext,
    ) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        for predicate in self.predicates:
            check_result = await predicate.check(target, context)
            if check_result.passed:
                result.passed_checks.append(predicate.name)
            else:
                result.is_valid = False
                result.failed_checks.append(f"{predicate.name}: {check_result.message}")
        
        return result

# 에이전트 매처
class AgentMatcher(IMatcher[SessionRow]):
    """세션에 적합한 에이전트를 찾는 매처"""
    
    def __init__(self, agent_selector: AbstractAgentSelector):
        self.agent_selector = agent_selector
    
    async def match(
        self,
        target: SessionRow,
        resources: list[AgentRow],
        context: MatchingContext,
    ) -> Optional[ResourceMatch]:
        # 아키텍처 호환성 체크
        compatible_agents = [
            ag for ag in resources 
            if ag.architecture == target.main_kernel.architecture
        ]
        
        # 에이전트 선택
        agent_id = await self.agent_selector.assign_agent_for_session(
            compatible_agents,
            target
        )
        
        if agent_id:
            agent = next(ag for ag in resources if ag.id == agent_id)
            return ResourceMatch(
                target=target,
                resource=agent,
                allocation_plan={'slots': target.requested_slots}
            )
        return None

# 리소스 할당기
class ResourceAllocator(IAllocator):
    """실제 리소스 할당을 처리"""
    
    def __init__(self, repository: ScheduleRepository):
        self.repository = repository
    
    async def allocate(
        self,
        match: ResourceMatch,
        context: AllocationContext,
    ) -> AllocationResult:
        try:
            agent_alloc_ctx = await self.repository.reserve_agent(
                context.scaling_group,
                match.resource.id,
                match.allocation_plan['slots']
            )
            
            return AllocationResult(
                success=True,
                allocated_resources={'agent_alloc_ctx': agent_alloc_ctx}
            )
        except Exception as e:
            return AllocationResult(
                success=False,
                allocated_resources=None,
                error=str(e)
            )
```

### 4. 통합 스케줄러

```python
class IntegratedScheduler:
    """세분화된 인터페이스들을 조합하여 전체 스케줄링 수행"""
    
    def __init__(
        self,
        selector: ISelector[SessionRow],
        validator: IValidator[SessionRow],
        matcher: IMatcher[SessionRow],
        allocator: IAllocator,
        finalizer: IFinalizer[SessionRow],
    ):
        self.selector = selector
        self.validator = validator
        self.matcher = matcher
        self.allocator = allocator
        self.finalizer = finalizer
    
    async def schedule_sessions(
        self,
        pending_sessions: list[SessionRow],
        available_agents: list[AgentRow],
        context: SchedulingContext,
    ) -> list[SchedulingResult]:
        results = []
        
        while pending_sessions:
            # 1. 세션 선택
            with self.schedule_stage('scheduler.select'):
                selected = await self.selector.select(
                    pending_sessions,
                    SelectionContext(...)
                )
                if not selected:
                    break
            
            # 2. 검증
            with self.schedule_stage('scheduler.validate'):
                validation = await self.validator.validate(
                    selected,
                    ValidationContext(...)
                )
                if not validation.is_valid:
                    results.append(SchedulingResult(
                        session=selected,
                        status='failed',
                        reason=validation.failed_checks
                    ))
                    pending_sessions.remove(selected)
                    continue
            
            # 3. 매칭
            with self.schedule_stage('scheduler.match'):
                match = await self.matcher.match(
                    selected,
                    available_agents,
                    MatchingContext(...)
                )
                
                if not match:
                    results.append(SchedulingResult(
                        session=selected,
                        status='no_resource',
                        reason='No suitable agent found'
                    ))
                    continue
            
            # 4. 할당
            with self.schedule_stage('scheduler.allocate'):
                allocation = await self.allocator.allocate(
                    match,
                    AllocationContext(...)
                )
                if allocation.failed:
                    results.append(SchedulingResult(
                        session=selected,
                        status='allocation_failed',
                        reason=allocation.error
                    ))
                    continue
                
            with self.schedule_stage('scheduler.finalize'):
                # 5. 완료 처리
                await self.finalizer.finalize(
                    selected,
                    allocation,
                    FinalizationContext(...)
                )
                results.append(SchedulingResult(
                    session=selected,
                    status='scheduled',
                    allocated_to=match.resource
                ))
                pending_sessions.remove(selected)
            
        return results
```

### 5. KernelScheduler를 활용한 통합 방안

```python
# 커널 레벨 스케줄러
class KernelScheduler:
    """개별 커널을 스케줄링하는 내부 스케줄러"""
    
    def __init__(
        self,
        matcher: IMatcher[KernelRow],
        allocator: IAllocator,
    ):
        self.matcher = matcher
        self.allocator = allocator
    
    async def schedule_kernel(
        self,
        kernel: KernelRow,
        available_agents: list[AgentRow],
        context: SchedulingContext,
    ) -> KernelSchedulingResult:
        """개별 커널에 대한 스케줄링 수행"""
        
        # 커널에 적합한 에이전트 매칭
        match = await self.matcher.match(
            kernel,
            available_agents,
            context
        )
        
        if not match:
            return KernelSchedulingResult(
                kernel=kernel,
                success=False,
                reason="No suitable agent found"
            )
        
        # 리소스 할당
        allocation = await self.allocator.allocate(
            match,
            AllocationContext(
                scaling_group=context.scaling_group,
                requested_slots=kernel.requested_slots
            )
        )
        
        if allocation.success:
            return KernelSchedulingResult(
                kernel=kernel,
                success=True,
                agent_alloc_ctx=allocation.allocated_resources['agent_alloc_ctx']
            )
        else:
            return KernelSchedulingResult(
                kernel=kernel,
                success=False,
                reason=allocation.error
            )

# 통합된 세션 스케줄러
class UnifiedSessionScheduler(IntegratedScheduler):
    """Single/Multi Node를 통합 처리하는 스케줄러"""
    
    def __init__(
        self,
        selector: ISelector[SessionRow],
        validator: IValidator[SessionRow],
        session_matcher: IMatcher[SessionRow],
        kernel_scheduler: KernelScheduler,
        allocator: IAllocator,
        finalizer: IFinalizer[SessionRow],
    ):
        super().__init__(selector, validator, session_matcher, allocator, finalizer)
        self.kernel_scheduler = kernel_scheduler
    
    async def _schedule_session(
        self,
        session: SessionRow,
        available_agents: list[AgentRow],
        context: SchedulingContext,
    ) -> SessionSchedulingResult:
        """ClusterMode에 따라 적절한 스케줄링 수행"""
        
        if session.cluster_mode == ClusterMode.SINGLE_NODE:
            # Single Node: 세션 전체를 하나의 에이전트에 할당
            return await self._schedule_single_node(session, available_agents, context)
        else:
            # Multi Node: KernelScheduler를 사용하여 각 커널 개별 스케줄링
            return await self._schedule_multi_node(session, available_agents, context)
    
    async def _schedule_single_node(
        self,
        session: SessionRow,
        available_agents: list[AgentRow],
        context: SchedulingContext,
    ) -> SessionSchedulingResult:
        """Single Node 세션 스케줄링"""
        
        # 세션 레벨 매칭
        match = await self.matcher.match(session, available_agents, context)
        if not match:
            return SessionSchedulingResult(
                session=session,
                success=False,
                reason="No suitable agent for session"
            )
        
        # 세션 전체 리소스 할당
        allocation = await self.allocator.allocate(
            match,
            AllocationContext(
                scaling_group=context.scaling_group,
                requested_slots=session.requested_slots
            )
        )
        
        if allocation.success:
            return SessionSchedulingResult(
                session=session,
                success=True,
                allocations=[allocation]
            )
        else:
            return SessionSchedulingResult(
                session=session,
                success=False,
                reason=allocation.error
            )
    
    async def _schedule_multi_node(
        self,
        session: SessionRow,
        available_agents: list[AgentRow],
        context: SchedulingContext,
    ) -> SessionSchedulingResult:
        """Multi Node 세션 스케줄링 - KernelScheduler 활용"""
        
        kernel_results = []
        allocated_agents = set()
        
        # 각 커널을 KernelScheduler로 처리
        for kernel in session.kernels:
            # 이미 할당된 에이전트 제외
            remaining_agents = [
                ag for ag in available_agents 
                if ag.id not in allocated_agents
            ]
            
            result = await self.kernel_scheduler.schedule_kernel(
                kernel,
                remaining_agents,
                context
            )
            
            if not result.success:
                # 하나라도 실패하면 전체 롤백
                return SessionSchedulingResult(
                    session=session,
                    success=False,
                    reason=f"Failed to schedule kernel {kernel.id}: {result.reason}",
                    kernel_results=kernel_results  # 디버깅용
                )
            
            kernel_results.append(result)
            if result.agent_alloc_ctx:
                allocated_agents.add(result.agent_alloc_ctx.agent_id)
        
        # 모든 커널 스케줄링 성공
        return SessionSchedulingResult(
            session=session,
            success=True,
            kernel_results=kernel_results
        )
```

### 6. 장점

1. **코드 재사용**: KernelScheduler가 커널 레벨 로직을 캡슐화
2. **일관된 인터페이스**: Single/Multi Node 모두 동일한 인터페이스로 처리
3. **책임 분리**: 세션 스케줄링과 커널 스케줄링이 명확히 분리
4. **확장성**: 새로운 ClusterMode 추가 시 쉽게 확장 가능
5. **테스트 용이성**: KernelScheduler를 독립적으로 테스트 가능

### 7. 구현 예시

```python
# 팩토리에서 통합 스케줄러 생성
class SchedulerFactory:
    def create_unified_scheduler(self, sgroup_opts: ScalingGroupOpts) -> UnifiedSessionScheduler:
        # 커널 레벨 컴포넌트
        kernel_matcher = KernelAgentMatcher(agent_selector)
        kernel_allocator = ResourceAllocator(repository)
        kernel_scheduler = KernelScheduler(kernel_matcher, kernel_allocator)
        
        # 세션 레벨 컴포넌트
        session_selector = SessionSelector(strategy)
        session_validator = SessionValidator(predicates)
        session_matcher = SessionAgentMatcher(agent_selector)
        session_finalizer = SessionFinalizer(repository, event_producer)
        
        return UnifiedSessionScheduler(
            selector=session_selector,
            validator=session_validator,
            session_matcher=session_matcher,
            kernel_scheduler=kernel_scheduler,
            allocator=ResourceAllocator(repository),
            finalizer=session_finalizer
        )
```

## 장점

1. **명확한 책임 분리**: 각 단계가 독립적인 인터페이스로 분리
2. **조합 가능성**: 다양한 구현체를 조합하여 새로운 스케줄링 전략 구성
3. **테스트 용이성**: 각 단계를 독립적으로 테스트 가능
4. **확장성**: 새로운 검증 규칙, 매칭 전략 등을 쉽게 추가
5. **재사용성**: 동일한 인터페이스를 다른 스케줄링 시나리오에도 활용 가능

## 구현 계획

1. **1단계**: 인터페이스 정의 및 기존 코드 분석
2. **2단계**: 각 인터페이스의 기본 구현체 작성
3. **3단계**: `IntegratedScheduler`로 통합 및 테스트
4. **4단계**: `SchedulerDispatcher` 리팩토링
5. **5단계**: 특화된 구현체 추가 (GPU, 비용 최적화 등)