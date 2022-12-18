from __future__ import annotations

import enum
from typing import (
    TYPE_CHECKING,
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

import attrs

if TYPE_CHECKING:
    from ai.backend.common.bgtask import BackgroundTaskManager
    from ai.backend.common.events import EventDispatcher, EventProducer

    # from .models.utils import ExtendedAsyncSAEngine


@attrs.define(slots=True, auto_attribs=True, init=False)
class MachineContext:
    # db: ExtendedAsyncSAEngine
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    background_task_manager: BackgroundTaskManager


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

    def __str__(self) -> str:
        return f"src: {self.src}, dst: {self.dst}, event: {self.event}"


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
        self.transitions.extend(transitions)
        self.transition_map = {t.event: t for t in self.transitions}

    async def trigger(self, state: State, event: TransitionEvent) -> Optional[State]:
        if state not in self.states:
            return None
        trsn = self.transition_map.get(event)
        if trsn is None:
            return None
        assert isinstance(trsn, Transition)
        if trsn.guard is not None:
            if not (await trsn.guard(ctx=self.ctx)):
                # TODO: log the result of guard
                return None
        if trsn.action is not None:
            await trsn.action(ctx=self.ctx)
        return trsn.dst
