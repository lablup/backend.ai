from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import UserDict, namedtuple
from contextvars import ContextVar
from decimal import Decimal
import enum
import ipaddress
import itertools
import math
import numbers
from pathlib import PurePosixPath
import sys
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    NewType,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    TYPE_CHECKING,
    Union,
    cast,
    overload,
)
import uuid

import aioredis
import aioredis.client
import aioredis.sentinel
import attr
import trafaret as t
import typeguard

__all__ = (
    'aobject',
    'JSONSerializableMixin',
    'DeviceId',
    'ContainerId',
    'SessionId',
    'KernelId',
    'MetricKey',
    'MetricValue',
    'MovingStatValue',
    'PID',
    'HostPID',
    'ContainerPID',
    'BinarySize',
    'HostPortPair',
    'DeviceId',
    'SlotName',
    'IntrinsicSlotNames',
    'ResourceSlot',
    'HardwareMetadata',
    'MountPermission',
    'MountPermissionLiteral',
    'MountTypes',
    'VFolderMount',
    'KernelCreationConfig',
    'KernelCreationResult',
    'ServicePortProtocols',
    'ClusterInfo',
    'ClusterMode',
    'ClusterSSHKeyPair',
    'check_typed_dict',
    'EtcdRedisConfig',
    'RedisConnectionInfo',
)

if TYPE_CHECKING:
    from .docker import ImageRef


T_aobj = TypeVar('T_aobj', bound='aobject')

current_resource_slots: ContextVar[Mapping[SlotName, SlotTypes]] = ContextVar('current_resource_slots')


class aobject(object):
    '''
    An "asynchronous" object which guarantees to invoke both ``def __init__(self, ...)`` and
    ``async def __ainit(self)__`` to ensure asynchronous initialization of the object.

    You can create an instance of subclasses of aboject in the following way:

    .. code-block:: python

       o = await SomeAObj.new(...)
    '''

    @classmethod
    async def new(cls: Type[T_aobj], *args, **kwargs) -> T_aobj:
        '''
        We can do ``await SomeAObject(...)``, but this makes mypy
        to complain about its return type with ``await`` statement.
        This is a copy of ``__new__()`` to workaround it.
        '''
        instance = super().__new__(cls)
        cls.__init__(instance, *args, **kwargs)
        await instance.__ainit__()
        return instance

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __ainit__(self) -> None:
        '''
        Automatically called when creating the instance using
        ``await SubclassOfAObject(...)``
        where the arguments are passed to ``__init__()`` as in
        the vanilla Python classes.
        '''
        pass


T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
T4 = TypeVar('T4')


@overload
def check_typed_tuple(
    value: Tuple[Any],
    types: Tuple[Type[T1]],
) -> Tuple[T1]:
    ...


@overload
def check_typed_tuple(
    value: Tuple[Any, Any],
    types: Tuple[Type[T1], Type[T2]],
) -> Tuple[T1, T2]:
    ...


@overload
def check_typed_tuple(
    value: Tuple[Any, Any, Any],
    types: Tuple[Type[T1], Type[T2], Type[T3]],
) -> Tuple[T1, T2, T3]:
    ...


@overload
def check_typed_tuple(
    value: Tuple[Any, Any, Any, Any],
    types: Tuple[Type[T1], Type[T2], Type[T3], Type[T4]],
) -> Tuple[T1, T2, T3, T4]:
    ...


def check_typed_tuple(value: Tuple[Any, ...], types: Tuple[Type, ...]) -> Tuple:
    for val, typ in itertools.zip_longest(value, types):
        if typ is not None:
            typeguard.check_type('item', val, typ)
    return value


TD = TypeVar('TD')


def check_typed_dict(value: Mapping[Any, Any], expected_type: Type[TD]) -> TD:
    """
    Validates the given dict against the given TypedDict class,
    and wraps the value as the given TypedDict type.

    This is a shortcut to :func:`typeguard.check_typed_dict()` function to fill extra information

    Currently using this function may not be able to fix type errors, due to an upstream issue:
    python/mypy#9827
    """
    assert issubclass(expected_type, dict) and hasattr(expected_type, '__annotations__'), \
           f"expected_type ({type(expected_type)}) must be a TypedDict class"
    frame = sys._getframe(1)
    _globals = frame.f_globals
    _locals = frame.f_locals
    memo = typeguard._TypeCheckMemo(_globals, _locals)
    typeguard.check_typed_dict('value', value, expected_type, memo)
    # Here we passed the check, so return it after casting.
    return cast(TD, value)


PID = NewType('PID', int)
HostPID = NewType('HostPID', PID)
ContainerPID = NewType('ContainerPID', PID)

ContainerId = NewType('ContainerId', str)
SessionId = NewType('SessionId', uuid.UUID)
KernelId = NewType('KernelId', uuid.UUID)
ImageAlias = NewType('ImageAlias', str)

AgentId = NewType('AgentId', str)
DeviceName = NewType('DeviceName', str)
DeviceId = NewType('DeviceId', str)
SlotName = NewType('SlotName', str)
MetricKey = NewType('MetricKey', str)

AccessKey = NewType('AccessKey', str)
SecretKey = NewType('SecretKey', str)


class LogSeverity(str, enum.Enum):
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DEBUG = 'debug'


class SlotTypes(str, enum.Enum):
    COUNT = 'count'
    BYTES = 'bytes'
    UNIQUE = 'unique'


class HardwareMetadata(TypedDict):
    status: Literal["healthy", "degraded", "offline", "unavailable"]
    status_info: Optional[str]
    metadata: Dict[str, str]


class AutoPullBehavior(str, enum.Enum):
    DIGEST = 'digest'
    TAG = 'tag'
    NONE = 'none'


class ServicePortProtocols(str, enum.Enum):
    HTTP = 'http'
    TCP = 'tcp'
    PREOPEN = 'preopen'


class SessionTypes(str, enum.Enum):
    INTERACTIVE = 'interactive'
    BATCH = 'batch'


class SessionResult(str, enum.Enum):
    UNDEFINED = 'undefined'
    SUCCESS = 'success'
    FAILURE = 'failure'


class ClusterMode(str, enum.Enum):
    SINGLE_NODE = 'single-node'
    MULTI_NODE = 'multi-node'


class MovingStatValue(TypedDict):
    min: str
    max: str
    sum: str
    avg: str
    diff: str
    rate: str
    version: Optional[int]  # for legacy client compatibility


MetricValue = TypedDict('MetricValue', {
    'current': str,
    'capacity': Optional[str],
    'pct': Optional[str],
    'unit_hint': str,
    'stats.min': str,
    'stats.max': str,
    'stats.sum': str,
    'stats.avg': str,
    'stats.diff': str,
    'stats.rate': str,
}, total=False)


class IntrinsicSlotNames(enum.Enum):
    CPU = SlotName('cpu')
    MEMORY = SlotName('mem')


class DefaultForUnspecified(str, enum.Enum):
    LIMITED = 'LIMITED'
    UNLIMITED = 'UNLIMITED'


class HandlerForUnknownSlotName(str, enum.Enum):
    DROP = 'drop'
    ERROR = 'error'


Quantum = Decimal('0.000')


class MountPermission(str, enum.Enum):
    READ_ONLY = 'ro'
    READ_WRITE = 'rw'
    RW_DELETE = 'wd'


MountPermissionLiteral = Literal['ro', 'rw', 'wd']


class MountTypes(str, enum.Enum):
    VOLUME = 'volume'
    BIND = 'bind'
    TMPFS = 'tmpfs'
    K8S_GENERIC = 'k8s-generic'
    K8S_HOSTPATH = 'k8s-hostpath'


class HostPortPair(namedtuple('HostPortPair', 'host port')):

    def as_sockaddr(self) -> Tuple[str, int]:
        return str(self.host), self.port

    def __str__(self) -> str:
        if isinstance(self.host, ipaddress.IPv6Address):
            return f'[{self.host}]:{self.port}'
        return f'{self.host}:{self.port}'


class BinarySize(int):
    '''
    A wrapper around Python integers to represent binary sizes for storage and
    memory in various places.

    Its string representation and parser, ``from_str()`` classmethod, does not use
    any locale-specific digit delimeters -- it supports only standard Python
    digit delimeters.
    '''

    suffix_map = {
        'y': 2 ** 80, 'Y': 2 ** 80,  # yotta
        'z': 2 ** 70, 'Z': 2 ** 70,  # zetta
        'e': 2 ** 60, 'E': 2 ** 60,  # exa
        'p': 2 ** 50, 'P': 2 ** 50,  # peta
        't': 2 ** 40, 'T': 2 ** 40,  # tera
        'g': 2 ** 30, 'G': 2 ** 30,  # giga
        'm': 2 ** 20, 'M': 2 ** 20,  # mega
        'k': 2 ** 10, 'K': 2 ** 10,  # kilo
        ' ': 1,
    }
    suffices = (' ', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    endings = ('ibytes', 'ibyte', 'ib', 'bytes', 'byte', 'b')

    @classmethod
    def _parse_str(cls, expr: str) -> Union[BinarySize, Decimal]:
        if expr.lower() in ('inf', 'infinite', 'infinity'):
            return Decimal('Infinity')
        orig_expr = expr
        expr = expr.strip().replace('_', '')
        try:
            return cls(expr)
        except ValueError:
            expr = expr.lower()
            dec_expr: Decimal
            try:
                for ending in cls.endings:
                    if expr.endswith(ending):
                        length = len(ending) + 1
                        suffix = expr[-length]
                        dec_expr = Decimal(expr[:-length])
                        break
                else:
                    # when there is suffix without scale (e.g., "2K")
                    if not str.isnumeric(expr[-1]):
                        suffix = expr[-1]
                        dec_expr = Decimal(expr[:-1])
                    else:
                        # has no suffix and is not an integer
                        # -> fractional bytes (e.g., 1.5 byte)
                        raise ValueError('Fractional bytes are not allowed')
            except ArithmeticError:
                raise ValueError('Unconvertible value', orig_expr)
            try:
                multiplier = cls.suffix_map[suffix]
            except KeyError:
                raise ValueError('Unconvertible value', orig_expr)
            return cls(dec_expr * multiplier)

    @classmethod
    def finite_from_str(
        cls,
        expr: Union[str, Decimal, numbers.Integral],
    ) -> BinarySize:
        if isinstance(expr, Decimal):
            if expr.is_infinite():
                raise ValueError('infinite values are not allowed')
            return cls(expr)
        if isinstance(expr, numbers.Integral):
            return cls(int(expr))
        result = cls._parse_str(expr)
        if isinstance(result, Decimal) and result.is_infinite():
            raise ValueError('infinite values are not allowed')
        return cls(int(result))

    @classmethod
    def from_str(
        cls,
        expr: Union[str, Decimal, numbers.Integral],
    ) -> Union[BinarySize, Decimal]:
        if isinstance(expr, Decimal):
            return cls(expr)
        if isinstance(expr, numbers.Integral):
            return cls(int(expr))
        return cls._parse_str(expr)

    def _preformat(self):
        scale = self
        suffix_idx = 0
        while scale >= 1024:
            scale //= 1024
            suffix_idx += 1
        return suffix_idx

    @staticmethod
    def _quantize(val, multiplier):
        d = Decimal(val) / Decimal(multiplier)
        if d == d.to_integral():
            value = d.quantize(Decimal(1))
        else:
            value = d.quantize(Decimal('.00')).normalize()
        return value

    def __str__(self):
        suffix_idx = self._preformat()
        if suffix_idx == 0:
            if self == 1:
                return f'{int(self)} byte'
            else:
                return f'{int(self)} bytes'
        else:
            suffix = type(self).suffices[suffix_idx]
            multiplier = type(self).suffix_map[suffix]
            value = self._quantize(self, multiplier)
            return f'{value} {suffix.upper()}iB'

    def __format__(self, format_spec):
        if len(format_spec) != 1:
            raise ValueError('format-string for BinarySize can be only one character.')
        if format_spec == 's':
            # automatically scaled
            suffix_idx = self._preformat()
            if suffix_idx == 0:
                return f'{int(self)}'
            suffix = type(self).suffices[suffix_idx]
            multiplier = type(self).suffix_map[suffix]
            value = self._quantize(self, multiplier)
            return f'{value}{suffix.lower()}'
        else:
            # use the given scale
            suffix = format_spec.lower()
            multiplier = type(self).suffix_map.get(suffix)
            if multiplier is None:
                raise ValueError('Unsupported scale unit.', suffix)
            value = self._quantize(self, multiplier)
            return f'{value}{suffix.lower()}'.strip()


class ResourceSlot(UserDict):

    __slots__ = ('data', )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def sync_keys(self, other: ResourceSlot) -> None:
        self_only_keys = self.data.keys() - other.data.keys()
        other_only_keys = other.data.keys() - self.data.keys()
        for k in self_only_keys:
            other.data[k] = Decimal(0)
        for k in other_only_keys:
            self.data[k] = Decimal(0)

    def __add__(self, other: ResourceSlot) -> ResourceSlot:
        assert isinstance(other, ResourceSlot), 'Only can add ResourceSlot to ResourceSlot.'
        self.sync_keys(other)
        return type(self)({
            k: self.get(k, 0) + other.get(k, 0)
            for k in (self.keys() | other.keys())
        })

    def __sub__(self, other: ResourceSlot) -> ResourceSlot:
        assert isinstance(other, ResourceSlot), 'Only can subtract ResourceSlot from ResourceSlot.'
        self.sync_keys(other)
        return type(self)({
            k: self.data[k] - other.get(k, 0)
            for k in self.keys()
        })

    def __eq__(self, other: object) -> bool:
        if other is self:
            return True
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        self.sync_keys(other)
        self_values = [self.data[k] for k in sorted(self.data.keys())]
        other_values = [other.data[k] for k in sorted(other.data.keys())]
        return self_values == other_values

    def __ne__(self, other: object) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        self.sync_keys(other)
        return not self.__eq__(other)

    def eq_contains(self, other: ResourceSlot) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        common_keys = sorted(other.keys() & self.keys())
        only_other_keys = other.keys() - self.keys()
        self_values = [self.data[k] for k in common_keys]
        other_values = [other.data[k] for k in common_keys]
        return self_values == other_values and all(other[k] == 0 for k in only_other_keys)

    def eq_contained(self, other: ResourceSlot) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        common_keys = sorted(other.keys() & self.keys())
        only_self_keys = self.keys() - other.keys()
        self_values = [self.data[k] for k in common_keys]
        other_values = [other.data[k] for k in common_keys]
        return self_values == other_values and all(self[k] == 0 for k in only_self_keys)

    def __le__(self, other: ResourceSlot) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        self.sync_keys(other)
        self_values = [self.data[k] for k in self.keys()]
        other_values = [other.data[k] for k in self.keys()]
        return not any(s > o for s, o in zip(self_values, other_values))

    def __lt__(self, other: ResourceSlot) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        self.sync_keys(other)
        self_values = [self.data[k] for k in self.keys()]
        other_values = [other.data[k] for k in self.keys()]
        return (not any(s > o for s, o in zip(self_values, other_values)) and
                not (self_values == other_values))

    def __ge__(self, other: ResourceSlot) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        self.sync_keys(other)
        self_values = [self.data[k] for k in other.keys()]
        other_values = [other.data[k] for k in other.keys()]
        return not any(s < o for s, o in zip(self_values, other_values))

    def __gt__(self, other: ResourceSlot) -> bool:
        assert isinstance(other, ResourceSlot), 'Only can compare ResourceSlot objects.'
        self.sync_keys(other)
        self_values = [self.data[k] for k in other.keys()]
        other_values = [other.data[k] for k in other.keys()]
        return (not any(s < o for s, o in zip(self_values, other_values)) and
                not (self_values == other_values))

    def normalize_slots(self, *, ignore_unknown: bool) -> ResourceSlot:
        known_slots = current_resource_slots.get()
        unset_slots = known_slots.keys() - self.data.keys()
        if not ignore_unknown and (unknown_slots := self.data.keys() - known_slots.keys()):
            raise ValueError('Unknown slots', unknown_slots)
        data = {
            k: v for k, v in self.data.items()
            if k in known_slots
        }
        for k in unset_slots:
            data[k] = Decimal(0)
        return type(self)(data)

    @classmethod
    def _normalize_value(cls, value: Any, unit: str) -> Decimal:
        try:
            if unit == 'bytes':
                if isinstance(value, Decimal):
                    return Decimal(value) if value.is_finite() else value
                if isinstance(value, int):
                    return Decimal(value)
                value = Decimal(BinarySize.from_str(value))
            else:
                value = Decimal(value)
                if value.is_finite():
                    value = value.quantize(Quantum).normalize()
        except ArithmeticError:
            raise ValueError('Cannot convert to decimal', value)
        return value

    @classmethod
    def _humanize_value(cls, value: Decimal, unit: str) -> str:
        if unit == 'bytes':
            try:
                result = '{:s}'.format(BinarySize(value))
            except (OverflowError, ValueError):
                result = _stringify_number(value)
        else:
            result = _stringify_number(value)
        return result

    @classmethod
    def _guess_slot_type(cls, key: str) -> str:
        if 'mem' in key:
            return 'bytes'
        return 'count'

    @classmethod
    def from_policy(cls, policy: Mapping[str, Any], slot_types: Mapping) -> 'ResourceSlot':
        try:
            data = {
                k: cls._normalize_value(v, slot_types[k])
                for k, v in policy['total_resource_slots'].items()
                if v is not None and k in slot_types
            }
            # fill missing (depending on the policy for unspecified)
            fill = Decimal(0)
            if policy['default_for_unspecified'] == DefaultForUnspecified.UNLIMITED:
                fill = Decimal('Infinity')
            for k in slot_types.keys():
                if k not in data:
                    data[k] = fill
        except KeyError as e:
            raise ValueError('unit unknown for slot', e.args[0])
        return cls(data)

    @classmethod
    def from_user_input(cls, obj: Mapping[str, Any], slot_types: Optional[Mapping]) -> 'ResourceSlot':
        try:
            if slot_types is None:
                data = {
                    k: cls._normalize_value(v, cls._guess_slot_type(k)) for k, v in obj.items()
                    if v is not None
                }
            else:
                data = {
                    k: cls._normalize_value(v, slot_types[k]) for k, v in obj.items()
                    if v is not None
                }
                # fill missing
                for k in slot_types.keys():
                    if k not in data:
                        data[k] = Decimal(0)
        except KeyError as e:
            raise ValueError('unit unknown for slot', e.args[0])
        return cls(data)

    def to_humanized(self, slot_types: Mapping) -> Mapping[str, str]:
        try:
            return {
                k: type(self)._humanize_value(v, slot_types[k]) for k, v in self.data.items()
                if v is not None
            }
        except KeyError as e:
            raise ValueError('unit unknown for slot', e.args[0])

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> 'ResourceSlot':
        data = {
            k: Decimal(v) for k, v in obj.items()
            if v is not None
        }
        return cls(data)

    def to_json(self) -> Mapping[str, str]:
        return {
            k: _stringify_number(Decimal(v)) for k, v in self.data.items()
            if v is not None
        }


class JSONSerializableMixin(metaclass=ABCMeta):

    @abstractmethod
    def to_json(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> JSONSerializableMixin:
        return cls(**cls.as_trafaret().check(obj))

    @classmethod
    @abstractmethod
    def as_trafaret(cls) -> t.Trafaret:
        raise NotImplementedError


@attr.define(slots=True)
class VFolderMount(JSONSerializableMixin):
    name: str
    vfid: uuid.UUID
    vfsubpath: PurePosixPath
    host_path: PurePosixPath
    kernel_path: PurePosixPath
    mount_perm: MountPermission

    def to_json(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'vfid': str(self.vfid),
            'vfsubpath': str(self.vfsubpath),
            'host_path': str(self.host_path),
            'kernel_path': str(self.kernel_path),
            'mount_perm': self.mount_perm.value,
        }

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> VFolderMount:
        return cls(**cls.as_trafaret().check(obj))

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        from . import validators as tx
        return t.Dict({
            t.Key('name'): t.String,
            t.Key('vfid'): tx.UUID,
            t.Key('vfsubpath', default="."): tx.PurePath,
            t.Key('host_path'): tx.PurePath,
            t.Key('kernel_path'): tx.PurePath,
            t.Key('mount_perm'): tx.Enum(MountPermission),
        })


class ImageRegistry(TypedDict):
    name: str
    url: str
    username: Optional[str]
    password: Optional[str]


class ImageConfig(TypedDict):
    canonical: str
    architecture: str
    digest: str
    repo_digest: Optional[str]
    registry: ImageRegistry
    labels: Mapping[str, str]


class ServicePort(TypedDict):
    name: str
    protocol: ServicePortProtocols
    container_ports: Sequence[int]
    host_ports: Sequence[Optional[int]]


class ClusterInfo(TypedDict):
    mode: ClusterMode
    size: int
    replicas: Mapping[str, int]  # per-role kernel counts
    network_name: Optional[str]
    ssh_keypair: Optional[ClusterSSHKeyPair]


class ClusterSSHKeyPair(TypedDict):
    public_key: str   # OpenSSH authorized-keys compatible format
    private_key: str  # PEM-encoded string


class DeviceModelInfo(TypedDict):
    device_id: DeviceId
    model_name: str
    data: Mapping[str, Any]


class KernelCreationResult(TypedDict):
    id: KernelId
    container_id: ContainerId
    service_ports: Sequence[ServicePort]
    kernel_host: str
    resource_spec: Mapping[str, Any]
    attached_devices: Mapping[DeviceName, Sequence[DeviceModelInfo]]
    repl_in_port: int
    repl_out_port: int
    stdin_port: int     # legacy
    stdout_port: int    # legacy


class KernelCreationConfig(TypedDict):
    image: ImageConfig
    auto_pull: AutoPullBehavior
    session_type: SessionTypes
    cluster_mode: ClusterMode
    cluster_role: str       # the kernel's role in the cluster
    cluster_idx: int        # the kernel's index in the cluster
    cluster_hostname: str   # the kernel's hostname in the cluster
    resource_slots: Mapping[str, str]  # json form of ResourceSlot
    resource_opts: Mapping[str, str]   # json form of resource options
    environ: Mapping[str, str]
    mounts: Sequence[Mapping[str, Any]]  # list of serialized VFolderMount
    package_directory: Sequence[str]
    idle_timeout: int
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    internal_data: Optional[Mapping[str, Any]]
    preopen_ports: List[int]


class KernelEnqueueingConfig(TypedDict):
    image_ref: ImageRef
    cluster_role: str
    cluster_idx: int
    cluster_hostname: str
    creation_config: dict
    bootstrap_script: str
    startup_command: str


def _stringify_number(v: Union[BinarySize, int, float, Decimal]) -> str:
    '''
    Stringify a number, preventing unwanted scientific notations.
    '''
    if isinstance(v, (float, Decimal)):
        if math.isinf(v) and v > 0:
            result = 'Infinity'
        elif math.isinf(v) and v < 0:
            result = '-Infinity'
        else:
            result = '{:f}'.format(v)
    elif isinstance(v, BinarySize):
        result = '{:d}'.format(int(v))
    elif isinstance(v, int):
        result = '{:d}'.format(v)
    else:
        result = str(v)
    return result


class Sentinel(enum.Enum):
    TOKEN = 0


class QueueSentinel(enum.Enum):
    CLOSED = 0
    TIMEOUT = 1


class EtcdRedisConfig(TypedDict, total=False):
    addr: Optional[HostPortPair]
    sentinel: Optional[Union[str, List[HostPortPair]]]
    service_name: Optional[str]
    password: Optional[str]


@attr.s(auto_attribs=True)
class RedisConnectionInfo:
    client: aioredis.Redis | aioredis.sentinel.Sentinel
    service_name: Optional[str]

    async def close(self) -> None:
        if isinstance(self.client, aioredis.Redis):
            await self.client.close()
