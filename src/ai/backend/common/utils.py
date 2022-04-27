from __future__ import annotations

import base64
from collections import OrderedDict
from datetime import timedelta
from itertools import chain
import numbers
import random
import re
import sys
from typing import (
    Any,
    Iterable,
    Iterator,
    Mapping,
    Tuple,
    TYPE_CHECKING,
    TypeVar,
    Union,
)
import uuid
if TYPE_CHECKING:
    from decimal import Decimal

# It is a bad practice to keep all "miscellaneous" stuffs
# into the single "utils" module.
# Let's categorize them by purpose and domain, and keep
# refactoring to use the proper module names.

from .asyncio import (  # for legacy imports  # noqa
    AsyncBarrier,
    cancel_tasks,
    current_loop,
    run_through,
)
from .enum_extension import StringSetFlag  # for legacy imports  # noqa
from .files import AsyncFileWriter  # for legacy imports  # noqa
from .networking import (  # for legacy imports  # noqa
    curl,
    find_free_port,
)
from .types import BinarySize


KT = TypeVar('KT')
VT = TypeVar('VT')


def env_info() -> str:
    """
    Returns a string that contains the Python version and runtime path.
    """
    v = sys.version_info
    pyver = f'Python {v.major}.{v.minor}.{v.micro}'
    if v.releaselevel == 'alpha':
        pyver += 'a'
    if v.releaselevel == 'beta':
        pyver += 'b'
    if v.releaselevel == 'candidate':
        pyver += 'rc'
    if v.releaselevel != 'final':
        pyver += str(v.serial)
    return f'{pyver} (env: {sys.prefix})'


def odict(*args: Tuple[KT, VT]) -> OrderedDict[KT, VT]:
    """
    A short-hand for the constructor of OrderedDict.
    :code:`odict(('a',1), ('b',2))` is equivalent to
    :code:`OrderedDict([('a',1), ('b',2)])`.
    """
    return OrderedDict(args)


def dict2kvlist(o: Mapping[KT, VT]) -> Iterable[Union[KT, VT]]:
    """
    Serializes a dict-like object into a generator of the flatten list of
    repeating key-value pairs.  It is useful when using HMSET method in Redis.

    Example:

       >>> list(dict2kvlist({'a': 1, 'b': 2}))
       ['a', 1, 'b', 2]
    """
    return chain.from_iterable((k, v) for k, v in o.items())


def generate_uuid() -> str:
    u = uuid.uuid4()
    # Strip the last two padding characters because u always has fixed length.
    return base64.urlsafe_b64encode(u.bytes)[:-2].decode('ascii')


def get_random_seq(length: float, num_points: int, min_distance: float) -> Iterator[float]:
    """
    Generate a random sequence of numbers within the range [0, length]
    with the given number of points and the minimum distance between the points.

    Note that X ( = the minimum distance d x the number of points N) must be equivalent to or smaller than
    the length L + d to guarantee the the minimum distance between the points.
    If X == L + d, the points are always equally spaced with d.

    :return: An iterator over the generated sequence
    """
    assert num_points * min_distance <= length + min_distance, \
           'There are too many points or it has a too large distance which cannot be fit into the given length.'
    extra = length - (num_points - 1) * min_distance
    ro = [random.uniform(0, 1) for _ in range(num_points + 1)]
    sum_ro = sum(ro)
    rn = [extra * r / sum_ro for r in ro[0:num_points]]
    spacing = [min_distance + rn[i] for i in range(num_points)]
    cumulative_sum = 0.0
    for s in spacing:
        cumulative_sum += s
        yield cumulative_sum - min_distance


def nmget(
    o: Mapping[str, Any],
    key_path: str,
    def_val: Any = None,
    path_delimiter: str = '.',
    null_as_default: bool = True,
) -> Any:
    """
    A short-hand for retrieving a value from nested mappings
    ("nested-mapping-get"). At each level it checks if the given "path"
    component in the given key exists and return the default value whenever
    fails.

    Example:
    >>> o = {'a':{'b':1}, 'x': None}
    >>> nmget(o, 'a', 0)
    {'b': 1}
    >>> nmget(o, 'a.b', 0)
    1
    >>> nmget(o, 'a/b', 0, '/')
    1
    >>> nmget(o, 'a.c', 0)
    0
    >>> nmget(o, 'x', 0)
    0
    >>> nmget(o, 'x', 0, null_as_default=False)
    None
    """
    pieces = key_path.split(path_delimiter)
    while pieces:
        p = pieces.pop(0)
        if o is None or p not in o:
            return def_val
        o = o[p]
    if o is None and null_as_default:
        return def_val
    return o


def readable_size_to_bytes(expr: Any) -> BinarySize | Decimal:
    if isinstance(expr, numbers.Real):
        return BinarySize(expr)
    return BinarySize.from_str(expr)


def str_to_timedelta(tstr: str) -> timedelta:
    """
    Convert humanized timedelta string into a Python timedelta object.

    Example:
    >>> str_to_timedelta('30min')
    datetime.timedelta(seconds=1800)
    >>> str_to_timedelta('1d1hr')
    datetime.timedelta(days=1, seconds=3600)
    >>> str_to_timedelta('2hours 15min')
    datetime.timedelta(seconds=8100)
    >>> str_to_timedelta('20sec')
    datetime.timedelta(seconds=20)
    >>> str_to_timedelta('300')
    datetime.timedelta(seconds=300)
    >>> str_to_timedelta('-1day')
    datetime.timedelta(days=-1)
    """
    _rx = re.compile(r'(?P<sign>[+|-])?\s*'
                     r'((?P<days>\d+(\.\d+)?)(d|day|days))?\s*'
                     r'((?P<hours>\d+(\.\d+)?)(h|hr|hrs|hour|hours))?\s*'
                     r'((?P<minutes>\d+(\.\d+)?)(m|min|mins|minute|minutes))?\s*'
                     r'((?P<seconds>\d+(\.\d+)?)(s|sec|secs|second|seconds))?$')
    match = _rx.match(tstr)
    if not match:
        try:
            return timedelta(seconds=float(tstr))  # consider bare number string as seconds
        except TypeError:
            pass
        raise ValueError('Invalid time expression')
    groups = match.groupdict()
    sign = groups.pop('sign', None)
    if set(groups.values()) == {None}:
        raise ValueError('Invalid time expression')
    params = {n: -float(t) if sign == '-' else float(t) for n, t in groups.items() if t}
    return timedelta(**params)  # type: ignore


class FstabEntry:
    """
    Entry class represents a non-comment line on the `fstab` file.
    """
    def __init__(self, device, mountpoint, fstype, options, d=0, p=0) -> None:
        self.device = device
        self.mountpoint = mountpoint
        self.fstype = fstype
        if not options:
            options = 'defaults'
        self.options = options
        self.d = d
        self.p = p

    def __eq__(self, o):
        return str(self) == str(o)

    def __str__(self):
        return "{} {} {} {} {} {}".format(self.device,
                                          self.mountpoint,
                                          self.fstype,
                                          self.options,
                                          self.d,
                                          self.p)


class Fstab:
    """
    Reader/writer for fstab file.
    Takes aiofile pointer for async I/O. It should be writable if add/remove
    operations are needed.

    NOTE: This class references Jorge Niedbalski R.'s gist snippet.
          We have been converted it to be compatible with Python 3
          and to support async I/O.
          (https://gist.github.com/niedbalski/507e974ed2d54a87ad37)
    """
    def __init__(self, fp) -> None:
        self._fp = fp

    def _hydrate_entry(self, line):
        return FstabEntry(*[x for x in line.strip('\n').split(' ') if x not in ('', None)])

    async def get_entries(self):
        await self._fp.seek(0)
        for line in await self._fp.readlines():
            try:
                line = line.strip()
                if not line.startswith("#"):
                    yield self._hydrate_entry(line)
            except TypeError:
                pass

    async def get_entry_by_attr(self, attr, value):
        async for entry in self.get_entries():
            e_attr = getattr(entry, attr)
            if e_attr == value:
                return entry
        return None

    async def add_entry(self, entry):
        if await self.get_entry_by_attr('device', entry.device):
            return False
        await self._fp.write(str(entry) + '\n')
        await self._fp.truncate()
        return entry

    async def add(self, device, mountpoint, fstype, options=None, d=0, p=0):
        return await self.add_entry(FstabEntry(device, mountpoint, fstype, options, d, p))

    async def remove_entry(self, entry):
        await self._fp.seek(0)
        lines = await self._fp.readlines()
        found = False
        for index, line in enumerate(lines):
            try:
                if not line.strip().startswith("#"):
                    if self._hydrate_entry(line) == entry:
                        found = True
                        break
            except TypeError:
                pass
        if not found:
            return False
        lines.remove(line)
        await self._fp.seek(0)
        await self._fp.write(''.join(lines))
        await self._fp.truncate()
        return True

    async def remove_by_mountpoint(self, mountpoint):
        entry = await self.get_entry_by_attr('mountpoint', mountpoint)
        if entry:
            return await self.remove_entry(entry)
        return False
