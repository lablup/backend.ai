from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import StrEnum
from typing import Awaitable, Callable, Coroutine, Generic, Optional, Protocol, Sequence, TypeVar

from tenacity import AsyncRetrying


class UnregisteredState(Exception):
    """
    The state not found in the state machine or in Transition
    """


class StateRegisterErr(Exception):
    pass


class BaseMachineContext:
    """
    The context of state machine which does not change during the life cycle.
    Every context of one manager are the same.
    """


class BaseStateContext:
    """
    The context of a state which contains extra information of a state.
    """


class BaseStateName(StrEnum):
    pass


class BaseTrigger(StrEnum):
    pass


class StateCoroutine(Protocol):
    def __call__(
        self, ctx: BaseMachineContext, state_ctx: Optional[BaseStateContext]
    ) -> Awaitable[Optional[BaseStateContext]]:
        ...


class TransitionGuard(Protocol):
    def __call__(
        self, *, ctx: BaseMachineContext, state_ctx: Optional[BaseStateContext]
    ) -> Awaitable[bool]:
        ...


class TransitionAction(Protocol):
    def __call__(
        self, *, ctx: BaseMachineContext, state_ctx: Optional[BaseStateContext]
    ) -> Awaitable[None]:
        ...


# StateCoroutine = Callable[
#     [BaseMachineContext, Optional[BaseStateContext]], Awaitable[Optional[BaseStateContext]]
# ]
StateNameType = TypeVar("StateNameType", bound=BaseStateName)


class State(Generic[StateNameType]):
    state_name: BaseStateName
    data: Optional[BaseStateContext]
    coro_factory: Optional[StateCoroutine]
    retry: Optional[AsyncRetrying]

    def __init__(
        self,
        state_name: BaseStateName,
        coro_factory: Optional[StateCoroutine] = None,
        data: Optional[BaseStateContext] = None,
        retry: Optional[AsyncRetrying] = None,
    ) -> None:
        self.state_name = state_name
        self.coro_factory = coro_factory
        self.data = data
        self.retry = retry

    def __str__(self) -> str:
        return str(self.state_name)

    def __repr__(self) -> str:
        return f"{self.state_name}: {self.state_name.value}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            raise ValueError(
                f"Invalid type to compare equal. expected `State` type, got {type(other)} type"
            )
        return self.state_name == other.state_name


class Transition:
    src: Sequence[tuple[State, BaseTrigger]]
    dst: State
    guard: Optional[TransitionGuard]
    action: Optional[TransitionAction]

    def __init__(
        self,
        src: Sequence[tuple[State, BaseTrigger]],
        dst: State[StateNameType],
        guard: Optional[TransitionGuard] = None,
        action: Optional[TransitionAction] = None,
    ) -> None:
        self.src = src
        self.dst = dst
        self.guard = guard
        self.action = action

    def __str__(self) -> str:
        return f"src: {self.src}, dst: {self.dst}"


class AsyncStateMachine(metaclass=ABCMeta):
    ctx: BaseMachineContext
    states: set[State]
    initial_state: State
    success_state: State
    failure_state: State
    current_state: State
    fallback_exception_handler: Optional[Callable[..., Coroutine[None, None, None]]]
    transition_map: dict[State, dict[BaseTrigger, Transition]]

    def __init__(
        self,
        ctx: BaseMachineContext,
        states: Sequence[State[StateNameType]],
        transitions: Sequence[Transition],
        *,
        initial_state: State,
        success_state: State,
        failure_state: State,
        fallback_exception_handler: Optional[Callable[..., Coroutine[None, None, None]]],
    ) -> None:
        self.ctx = ctx

        self._register_state(states)
        self._register_transition(transitions)
        self._init_states(initial_state, success_state, failure_state)
        self.fallback_exception_handler = fallback_exception_handler

    def _register_state(self, states: Sequence[State[StateNameType]]) -> None:
        for s in states:
            if s in self.states:
                raise StateRegisterErr(f"State {s} is already registered")
            self.states.add(s)

    def _register_transition(self, transitions: Sequence[Transition]) -> None:
        for t in transitions:
            if t.dst not in self.states:
                raise UnregisteredState(f"{t.dst} is not registered in this state machine")
            if t.dst not in self.transition_map:
                self.transition_map[t.dst] = {}
            sources = t.src
            for src, trigger in sources:
                if src not in self.states:
                    raise UnregisteredState(f"{src} is not registered in this state machine")
                if src not in self.transition_map:
                    self.transition_map[src] = {}
                if trigger not in self.transition_map[src]:
                    self.transition_map[src][trigger] = t

    def _init_states(
        self, initial_state: State, success_state: State, failure_state: State
    ) -> None:
        def _check(cand_state: State) -> State:
            if cand_state not in self.states:
                raise UnregisteredState(f"{cand_state} is not registered in this state machine")
            return cand_state

        self.initial_state = _check(initial_state)
        self.success_state = _check(success_state)
        self.failure_state = _check(failure_state)
        self.current_state = initial_state

    async def trigger(
        self, trigger: BaseTrigger, new_state_ctx: Optional[BaseStateContext] = None
    ) -> State:
        """
        Trigger a transition from current state.
        If there is no transition for the current state, raise error.
        `new_state_ctx` is the result of the current state's coroutine, which is passed to a destination state.
        """
        cand_transitions = self.transition_map.get(self.current_state)
        if cand_transitions is None:
            raise UnregisteredState
        trsn = cand_transitions.get(trigger)
        if trsn is None:
            raise UnregisteredState
        if trsn.action is not None:
            await trsn.action(ctx=self.ctx, state_ctx=self.current_state.data)
        dst = trsn.dst
        if new_state_ctx is not None:
            dst.data = new_state_ctx
        return dst

    @abstractmethod
    async def run(self) -> None:
        """
        Run state machine from initial state.
        """
        raise NotImplementedError
