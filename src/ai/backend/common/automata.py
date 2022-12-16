from __future__ import annotations

import enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Protocol,
    TypeVar,
)


class MachineContext:
    pass


class UnregisteredState(Exception):
    """
    The state not found in the state machine or in Transition
    """


class StateRegisterErr(Exception):
    pass


class DuplicateTransitionEvent(Exception):
    """
    The event that trigger an event is already registered in the state machine
    """


class BaseStateName(str, enum.Enum):
    pass


class TransitionEvent:
    pass


class TransitionGuard(Protocol):
    def __call__(self, *, ctx: MachineContext) -> Awaitable[bool]:
        ...


class TransitionAction(Protocol):
    def __call__(self, *, ctx: MachineContext) -> Awaitable[None]:
        ...


StateNameType = TypeVar("StateNameType", bound=BaseStateName)


class State(Generic[StateNameType]):
    state_name: BaseStateName
    data: Dict[str, Any]
    coro_factory: Optional[Callable[..., Coroutine[None, None, bool]]]

    def __init__(
        self,
        state_name: BaseStateName,
        coro_factory: Optional[Callable[..., Coroutine[None, None, bool]]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.state_name = state_name
        self.coro_factory = coro_factory
        self.data = data or dict()

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
    src: State
    dst: State
    event: TransitionEvent
    guard: Optional[TransitionGuard]
    action: Optional[TransitionAction]
    ctx: Optional[MachineContext]

    def __init__(
        self,
        src: State[StateNameType],
        dst: State[StateNameType],
        event: TransitionEvent,
        guard: Optional[TransitionGuard] = None,
        action: Optional[TransitionAction] = None,
    ) -> None:
        self.src = src
        self.dst = dst
        self.event = event
        self.guard = guard
        self.action = action
        self.ctx = None

    def __str__(self) -> str:
        return f"src: {self.src}, dst: {self.dst}, event: {self.event}"

    async def trigger(self) -> None:
        assert self.ctx is not None
        if self.guard is not None:
            if not (await self.guard(ctx=self.ctx)):
                # TODO: log the result of guard
                return
        if self.action is not None:
            await self.action(ctx=self.ctx)


class AsyncStateMachine:
    ctx: MachineContext
    states: List[State]
    transitions: List[Transition]
    transition_map: Dict[TransitionEvent, Transition]

    def __init__(
        self,
        ctx: MachineContext,
        states: Iterable[State[StateNameType]],
        transitions: Iterable[Transition],
    ) -> None:
        self.ctx = ctx

        self._register_state(states)
        self._register_transition(transitions)

    def _register_state(self, states: Iterable[State[StateNameType]]) -> None:
        for s in states:
            if s in self.states:
                raise StateRegisterErr(f"State {s} is already registered")
        self.states.extend(states)

    def _register_transition(self, transitions: Iterable[Transition]) -> None:
        for t in transitions:
            if t.src not in self.states or t.dst not in self.states:
                raise UnregisteredState(
                    f"{t.src} or {t.dst} is not registered in this state machine"
                )
            if t.event in self.transition_map:
                raise DuplicateTransitionEvent(
                    f"Event {t.event} is already registered with transition {t}"
                )
            t.ctx = self.ctx
        self.transitions.extend(transitions)
        self.transition_map = {t.event: t for t in self.transitions}

    async def trigger(self, state: State, event: TransitionEvent) -> Optional[State]:
        if state not in self.states:
            return None
        trsn = self.transition_map.get(event)
        if trsn is None:
            return None
        assert isinstance(trsn, Transition)
        await trsn.trigger()
        return trsn.dst
