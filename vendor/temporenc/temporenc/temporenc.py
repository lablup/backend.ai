
import datetime
import struct
import sys


#
# Compatibility
#

PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[0:2] == (2, 6)


#
# Components and types
#

SUPPORTED_TYPES = set(['D', 'T', 'DT', 'DTZ', 'DTS', 'DTSZ'])

D_MASK = 0x1fffff
T_MASK = 0x1ffff
Z_MASK = 0x7f

YEAR_MAX, YEAR_EMPTY, YEAR_MASK = 4094, 4095, 0xfff
MONTH_MAX, MONTH_EMPTY, MONTH_MASK = 11, 15, 0xf
DAY_MAX, DAY_EMPTY, DAY_MASK = 30, 31, 0x1f
HOUR_MAX, HOUR_EMPTY, HOUR_MASK = 23, 31, 0x1f
MINUTE_MAX, MINUTE_EMPTY, MINUTE_MASK = 59, 63, 0x3f
SECOND_MAX, SECOND_EMPTY, SECOND_MASK = 60, 63, 0x3f
MILLISECOND_MAX, MILLISECOND_MASK = 999, 0x3ff
MICROSECOND_MAX, MICROSECOND_MASK = 999999, 0xfffff
NANOSECOND_MAX, NANOSECOND_MASK = 999999999, 0x3fffffff
TIMEZONE_MAX, TIMEZONE_EMPTY = 125, 127

D_LENGTH = 3
T_LENGTH = 3
DT_LENGTH = 5
DTZ_LENGTH = 6
DTS_LENGTHS = [7, 8, 9, 6]    # indexed by precision bits
DTSZ_LENGTHS = [8, 9, 10, 7]  # idem


#
# Helpers
#

pack_4 = struct.Struct('>L').pack
pack_8 = struct.Struct('>Q').pack
pack_2_8 = struct.Struct('>HQ').pack


def unpack_4(value, _unpack=struct.Struct('>L').unpack):
    return _unpack(value)[0]


def unpack_8(value, _unpack=struct.Struct('>Q').unpack):
    return _unpack(value)[0]


def _detect_type(first):
    """
    Detect type information from the numerical value of the first byte.
    """
    if first <= 0b00111111:
        return 'DT', None, DT_LENGTH
    elif first <= 0b01111111:
        precision = first >> 4 & 0b11
        return 'DTS', precision, DTS_LENGTHS[precision]
    elif first <= 0b10011111:
        return 'D', None, D_LENGTH
    elif first <= 0b10100001:
        return 'T', None, T_LENGTH
    elif first <= 0b10111111:
        return None, None, None
    elif first <= 0b11011111:
        return 'DTZ', None, DTZ_LENGTH
    elif first <= 0b11111111:
        precision = first >> 3 & 0b11
        return 'DTSZ', precision, DTSZ_LENGTHS[precision]


class FixedOffset(datetime.tzinfo):
    """Time zone information for a fixed offset from UTC."""

    # Python 2 does not have any concrete tzinfo implementations in its
    # standard library, hence this implementation. This implementation
    # is based on the examples in the Python docs, in particular:
    # https://docs.python.org/3.4/library/datetime.html#tzinfo-objects

    ZERO = datetime.timedelta(0)

    def __init__(self, minutes):
        self._offset = datetime.timedelta(minutes=minutes)
        sign = '+' if minutes >= 0 else '-'
        hours, minutes = divmod(minutes, 60)
        self._name = 'UTC{0}{1:02d}:{2:02d}'.format(sign, hours, minutes)

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return self.ZERO

    def __repr__(self):
        return '<{0}>'.format(self._name)


# This cache maps offsets in minutes to FixedOffset instances.
tzinfo_cache = {
    None: None,  # hack to simpify cached_tzinfo() callers
}


def cached_tzinfo(minutes):
    """
    Get a (cached) tzinfo instance for the specified offset in minutes.
    """
    try:
        tzinfo = tzinfo_cache[minutes]
    except KeyError:
        tzinfo_cache[minutes] = tzinfo = FixedOffset(minutes)
    return tzinfo


#
# Public API
#

class Moment(object):
    """
    Container to represent a parsed *temporenc* value.

    Each constituent part is accessible as an instance attribute. These
    are: ``year``, ``month``, ``day``, ``hour``, ``minute``, ``second``,
    ``millisecond``, ``microsecond``, ``nanosecond``, and ``tz_offset``.
    Since *temporenc* allows partial date and time information, any
    attribute can be ``None``.

    The attributes for sub-second precision form a group that is either
    completely empty (all attributes are ``None``) or completely filled
    (no attribute is ``None``).

    This class is intended to be a read-only immutable data structure;
    assigning new values to attributes is not supported.

    Instances are hashable and can be used as dictionary keys or as
    members of a set. Instances representing the same moment in time
    have the same hash value. Time zone information is not taken into
    account for hashing purposes, since time zone aware values must have
    their constituent parts in UTC.

    Instances of this class can be compared to each other, with earlier
    dates sorting first. As with hashing, time zone information is not
    taken into account, since the actual data must be in UTC in those
    cases.

    .. note::

       This class must not be instantiated directly; use one of the
       unpacking functions like :py:func:`unpackb()` instead.
    """
    __slots__ = [
        'year', 'month', 'day',
        'hour', 'minute', 'second',
        'millisecond', 'microsecond', 'nanosecond',
        'tz_offset',
        '_has_date', '_has_time', '_struct']

    def __init__(
            self,
            year, month, day,
            hour, minute, second, nanosecond,
            tz_offset):

        #: Year component.
        self.year = year

        #: Month component.
        self.month = month

        #: Day component.
        self.day = day

        #: Hour component.
        self.hour = hour

        #: Minute component.
        self.minute = minute

        #: Second component.
        self.second = second

        if nanosecond is None:
            self.millisecond = self.microsecond = self.nanosecond = None
        else:
            #: Millisecond component. If set, :py:attr:`microsecond` and
            #: :py:attr:`nanosecond` are also set.
            self.millisecond = nanosecond // 1000000

            #: Microsecond component. If set, :py:attr:`millisecond` and
            #: :py:attr:`nanosecond` are also set.
            self.microsecond = nanosecond // 1000

            #: Nanosecond component. If set, :py:attr:`millisecond` and
            #: :py:attr:`microsecond` are also set.
            self.nanosecond = nanosecond

        #: Time zone offset (total minutes). To calculate the hours and
        #: minutes, use ``h, m = divmod(offset, 60)``.
        self.tz_offset = tz_offset

        self._has_date = not (year is None and month is None and day is None)
        self._has_time = not (hour is None and minute is None
                              and second is None)

        # This 'struct' contains the values that are relevant for
        # comparison, hashing, and so on.
        self._struct = (
            self.year, self.month, self.day,
            self.hour, self.minute, self.second, self.nanosecond,
            self.tz_offset)

    def __str__(self):
        buf = []

        if self._has_date:
            buf.append("{0:04d}-".format(self.year)
                       if self.year is not None else "????-")
            buf.append("{0:02d}-".format(self.month)
                       if self.month is not None else "??-")
            buf.append("{0:02d}".format(self.day)
                       if self.day is not None else "??")

        if self._has_time:

            if self._has_date:
                buf.append(" ")  # separator

            buf.append("{0:02d}:".format(self.hour)
                       if self.hour is not None else "??:")
            buf.append("{0:02d}:".format(self.minute)
                       if self.minute is not None else "??:")
            buf.append("{0:02d}".format(self.second)
                       if self.second is not None else "??")

        if self.nanosecond is not None:
            if not self._has_time:
                # Weird edge case: empty hour/minute/second, but
                # sub-second precision is set.
                buf.append("??:??:??")

            if self.nanosecond == 0:
                buf.append('.0')
            else:
                buf.append(".{0:09d}".format(self.nanosecond).rstrip("0"))

        if self.tz_offset is not None:
            if self.tz_offset == 0:
                buf.append('Z')
            else:
                h, m = divmod(self.tz_offset, 60)
                sign = '+' if h >= 0 else '-'
                buf.append('{0}{1:02d}:{2:02d}'.format(sign, h, m))

        return ''.join(buf)

    def __repr__(self):
        return "<temporenc.Moment '{0}'>".format(self)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._struct == other._struct

    def __ne__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._struct != other._struct

    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._struct > other._struct

    def __ge__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._struct >= other._struct

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._struct < other._struct

    def __le__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._struct <= other._struct

    def __hash__(self):
        return hash(self._struct)

    def datetime(self, strict=True):
        """
        Convert this value to a ``datetime.datetime`` instance.

        Since the classes in the ``datetime`` module do not support
        missing values, this will fail when one of the required
        components is not set, which is indicated by raising
        a :py:exc:`ValueError`.

        The default is to perform a strict conversion. To ease working
        with partial dates and times, the `strict` argument can be set
        to `False`. In that case this method will try to convert the
        value anyway, by substituting a default value for any missing
        component, e.g. a missing time is set to `00:00:00`. Note that
        these substituted values are bogus and should not be used for
        any application logic, but at least this allows applications to
        use things like ``.strftime()`` on partial dates and times.

        The *temporenc* format allows inclusion of a time zone offset.
        When converting to a ``datetime`` instance, time zone
        information is handled as follows:

        * When no time zone information was present in the original data
          (e.g. when unpacking *temporenc* type ``DT``), the return
          value will be a naive `datetime` instance, i.e. its ``tzinfo``
          attribute is `None`.

        * If the original data did include time zone information, the
          return value will be a time zone aware instance, which means the
          instance will have a ``tzinfo`` attribute corresponding to
          the offset included in the value.

        :param bool strict: whether to use strict conversion rules
        :return: converted value
        :rtype: `datetime.datetime`
        """

        if strict:
            if None in (self.year, self.month, self.day):
                raise ValueError("incomplete date information")
            if None in (self.hour, self.minute, self.second):
                raise ValueError("incomplete time information")

        hour, minute, second = self.hour, self.minute, self.second
        year, month, day = self.year, self.month, self.day

        # The stdlib's datetime classes always specify microseconds.
        us = self.microsecond if self.microsecond is not None else 0

        if not strict:
            # Substitute defaults for missing values.
            if year is None:
                year = 1

            if month is None:
                month = 1

            if day is None:
                day = 1

            if hour is None:
                hour = 0

            if minute is None:
                minute = 0

            if second is None:
                second = 0
            elif second == 60:  # assume that this is a leap second
                second = 59

        dt = datetime.datetime(
            year, month, day,
            hour, minute, second, us,
            tzinfo=cached_tzinfo(self.tz_offset))

        return dt

    def date(self, strict=True):
        """
        Convert this value to a ``datetime.date`` instance.

        See the documentation for the :py:meth:`datetime()` method for
        more information.

        :param bool strict: whether to use strict conversion rules
        :param bool local: whether to convert to local time
        :return: converted value
        :rtype: `datetime.date`
        """
        if strict:
            if None in (self.year, self.month, self.day):
                raise ValueError("incomplete date information")

            # Shortcut for performance reasons
            return datetime.date(self.year, self.month, self.day)

        return self.datetime(strict=False).date()

    def time(self, strict=True):
        """
        Convert this value to a ``datetime.time`` instance.

        See the documentation for the :py:meth:`datetime()` method for
        more information.

        :param bool strict: whether to use strict conversion rules
        :param bool local: whether to convert to local time
        :return: converted value
        :rtype: `datetime.time`
        """
        if strict:
            if None in (self.hour, self.minute, self.second):
                raise ValueError("incomplete time information")

            # Shortcut for performance reasons
            return datetime.time(
                self.hour, self.minute, self.second,
                self.microsecond if self.microsecond is not None else 0,
                tzinfo=cached_tzinfo(self.tz_offset))

        return self.datetime(strict=False).timetz()


def packb(
        value=None, type=None,
        year=None, month=None, day=None,
        hour=None, minute=None, second=None,
        millisecond=None, microsecond=None, nanosecond=None,
        tz_offset=None):
    """
    Pack date and time information into a byte string.

    If specified, `value` must be a ``datetime.datetime``,
    ``datetime.date``, or ``datetime.time`` instance.

    The `type` specifies the *temporenc* type to use. Valid types are
    ``D``, ``T``, ``DT``, ``DTZ``, ``DTS``, or ``DTSZ``. If not
    specified, the most compact encoding that can represent the provided
    information will be determined automatically. Note that instances of
    the classes in the ``datetime`` module always use microsecond
    precision, so make sure to specify a more compact type if no
    sub-second precision is required.

    Most applications would only use the `value` and `type` arguments;
    the other arguments allow for encoding data that does not fit the
    conceptual date and time model used by the standard library's
    ``datetime`` module.

    .. note::

       Applications that require lexicographical ordering of encoded
       values should always explicitly specify a type to use.

    All other arguments can be used to specify individual pieces of
    information that make up a date or time. If both `value` and more
    specific fields are provided, the individual fields override the
    values extracted from `value`, e.g. ``packb(datetime.datetime.now(),
    minute=0, second=0)`` encodes the start of the current hour.

    The sub-second precision arguments (`millisecond`, `microsecond`,
    and `nanosecond`) must not be used together, since those are
    conceptually mutually exclusive.

    .. note::

       The `value` argument is the only positional argument. All other
       arguments *must* be specified as keyword arguments (even though
       this is not enforced because of Python 2 compatibility).

    :param value: instance of one of the ``datetime`` classes (optional)
    :param str type: *temporenc* type (optional)
    :param int year: year (optional)
    :param int month: month (optional)
    :param int day: day (optional)
    :param int hour: hour (optional)
    :param int minute: minute (optional)
    :param int second: second (optional)
    :param int millisecond: millisecond (optional)
    :param int microsecond: microsecond (optional)
    :param int nanosecond: nanosecond (optional)
    :param int tz_offset: time zone offset in minutes from UTC (optional)
    :return: encoded *temporenc* value
    :rtype: bytes
    """

    #
    # Native 'datetime' module handling
    #

    if value is not None:
        handled = False

        if isinstance(value, (datetime.datetime, datetime.time)):

            # Handle time zone information. Instances of the
            # datetime.datetime and datetime.time classes may have an
            # associated time zone. If an explicit tz_offset was
            # specified, that takes precedence.
            if tz_offset is None:
                delta = value.utcoffset()
                if delta is not None:
                    tz_offset = delta.days * 1440 + delta.seconds // 60

            # Extract time fields
            handled = True
            if hour is None:
                hour = value.hour
            if minute is None:
                minute = value.minute
            if second is None:
                second = value.second
            if (millisecond is None and microsecond is None
                    and nanosecond is None):
                microsecond = value.microsecond

        if isinstance(value, (datetime.datetime, datetime.date)):
            # Extract date fields
            handled = True
            if year is None:
                year = value.year
            if month is None:
                month = value.month
            if day is None:
                day = value.day

        if not handled:
            raise ValueError("Cannot encode {0!r}".format(value))

    #
    # Type detection
    #

    if type is None:
        has_d = not (year is None and month is None and day is None)
        has_t = not (hour is None and minute is None and second is None)
        has_s = not (millisecond is None and microsecond is None
                     and nanosecond is None)
        has_z = tz_offset is not None

        if has_z and has_s:
            type = 'DTSZ'
        elif has_z:
            type = 'DTZ'
        elif has_s:
            type = 'DTS'
        elif has_d and has_t:
            type = 'DT'
        elif has_d:
            type = 'D'
        elif has_t:
            type = 'T'
        else:
            # No information at all, just use the smallest type
            type = 'D'

    elif type not in SUPPORTED_TYPES:
        raise ValueError("invalid temporenc type: {0!r}".format(type))

    #
    # Value checking
    #

    if year is None:
        year = YEAR_EMPTY
    elif not 0 <= year <= YEAR_MAX:
        raise ValueError("year not within supported range")

    if month is None:
        month = MONTH_EMPTY
    else:
        month -= 1
        if not 0 <= month <= MONTH_MAX:
            raise ValueError("month not within supported range")

    if day is None:
        day = DAY_EMPTY
    else:
        day -= 1
        if not 0 <= day <= DAY_MAX:
            raise ValueError("day not within supported range")

    if hour is None:
        hour = HOUR_EMPTY
    elif not 0 <= hour <= HOUR_MAX:
        raise ValueError("hour not within supported range")

    if minute is None:
        minute = MINUTE_EMPTY
    elif not 0 <= minute <= MINUTE_MAX:
        raise ValueError("minute not within supported range")

    if second is None:
        second = SECOND_EMPTY
    elif not 0 <= second <= SECOND_MAX:
        raise ValueError("second not within supported range")

    if (millisecond is not None
            and not 0 <= millisecond <= MILLISECOND_MAX):
        raise ValueError("millisecond not within supported range")

    if (microsecond is not None
            and not 0 <= microsecond <= MICROSECOND_MAX):
        raise ValueError("microsecond not within supported range")

    if (nanosecond is not None
            and not 0 <= nanosecond <= NANOSECOND_MAX):
        raise ValueError("nanosecond not within supported range")

    if tz_offset is None:
        tz_offset = TIMEZONE_EMPTY
    else:
        z, remainder = divmod(tz_offset, 15)
        if remainder:
            raise ValueError("tz_offset must be a multiple of 15")
        z += 64
        if not 0 <= z <= TIMEZONE_MAX:
            raise ValueError("tz_offset not within supported range")

    #
    # Byte packing
    #

    d = year << 9 | month << 5 | day
    t = hour << 12 | minute << 6 | second

    if type == 'D':
        # 100DDDDD DDDDDDDD DDDDDDDD
        return pack_4(0b100 << 21 | d)[-3:]

    elif type == 'T':
        # 1010000T TTTTTTTT TTTTTTTT
        return pack_4(0b1010000 << 17 | t)[-3:]

    elif type == 'DT':
        # 00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT
        # TTTTTTTT
        return pack_8(d << 17 | t)[-5:]

    elif type == 'DTZ':
        # 110DDDDD DDDDDDDD DDDDDDDD TTTTTTTT
        # TTTTTTTT TZZZZZZZ
        return pack_8(0b110 << 45 | d << 24 | t << 7 | z)[-6:]

    elif type == 'DTS':
        if nanosecond is not None:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS
            return pack_2_8(
                0b0110 << 4 | d >> 17,
                (d & 0x1ffff) << 47 | t << 30 | nanosecond)[-9:]
        elif microsecond is not None:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSS00
            return pack_8(
                0b0101 << 60 | d << 39 | t << 22 | microsecond << 2)
        elif millisecond is not None:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSS0000
            return pack_8(
                0b0100 << 52 | d << 31 | t << 14 | millisecond << 4)[-7:]
        else:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TT000000
            return pack_8(0b0111 << 44 | d << 23 | t << 6)[-6:]

    elif type == 'DTSZ':
        if nanosecond is not None:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS SZZZZZZZ
            return pack_2_8(
                0b11110 << 11 | d >> 10,
                (d & 0x3ff) << 54 | t << 37 | nanosecond << 7 | z)
        elif microsecond is not None:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSZ
            # ZZZZZZ00
            return pack_2_8(
                0b11101 << 3 | d >> 18,
                (d & 0x3ffff) << 46 | t << 29 | microsecond << 9 | z << 2)[-9:]
        elif millisecond is not None:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSZZZ ZZZZ0000
            return pack_8(
                0b11100 << 59 | d << 38 | t << 21 | millisecond << 11 | z << 4)
        else:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTZZZZZ ZZ000000
            return pack_8(0b11111 << 51 | d << 30 | t << 13 | z << 6)[-7:]


def pack(fp, *args, **kwargs):
    """
    Pack date and time information and write it to a file-like object.

    This is a short-hand for writing a packed value directly to
    a file-like object. There is no additional behaviour. This function
    only exists for API parity with the :py:func:`unpack()` function.

    Except for the first argument (the file-like object), all arguments
    (both positional and keyword) are passed on to :py:func:`packb()`.
    See :py:func:`packb()` for more information.

    :param file-like fp: writeable file-like object
    :param args: propagated to :py:func:`packb()`
    :param kwargs: propagated to :py:func:`packb()`
    :return: number of bytes written
    :rtype: int
    """
    return fp.write(packb(*args, **kwargs))


def unpackb(value):
    """
    Unpack a *temporenc* value from a byte string.

    If no valid value could be read, this raises :py:exc:`ValueError`.

    :param bytes value: a byte string (or `bytearray`) to parse
    :return: a parsed *temporenc* structure
    :rtype: :py:class:`Moment`
    """

    #
    # Unpack components
    #

    first = value[0]

    if PY2 and isinstance(first, bytes):  # pragma: no cover
        first = ord(first)

    if PY26 and isinstance(value, bytearray):  # pragma: no cover
        # struct.unpack() does not handle bytearray() in Python < 2.7
        value = bytes(value)

    type, precision, expected_length = _detect_type(first)

    if type is None:
        raise ValueError("first byte does not contain a valid tag")

    if len(value) != expected_length:
        if precision is None:
            raise ValueError(
                "{0} value must be {1:d} bytes; got {2:d}".format(
                    type, expected_length, len(value)))
        else:
            raise ValueError(
                "{0} value with precision {1:02b} must be {2:d} bytes; "
                "got {3:d}".format(
                    type, precision, expected_length, len(value)))

    date = time = tz_offset = nanosecond = padding = None

    if type == 'D':
        # 100DDDDD DDDDDDDD DDDDDDDD
        date = unpack_4(b'\x00' + value) & D_MASK

    elif type == 'T':
        # 1010000T TTTTTTTT TTTTTTTT
        time = unpack_4(b'\x00' + value) & T_MASK

    elif type == 'DT':
        # 00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT
        # TTTTTTTT
        n = unpack_8(b'\x00\x00\x00' + value)
        date = n >> 17 & D_MASK
        time = n & T_MASK

    elif type == 'DTZ':
        # 110DDDDD DDDDDDDD DDDDDDDD TTTTTTTT
        # TTTTTTTT TZZZZZZZ
        n = unpack_8(b'\x00\x00' + value)
        date = n >> 24 & D_MASK
        time = n >> 7 & T_MASK
        tz_offset = n & Z_MASK

    elif type == 'DTS':
        # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
        # TTTTTTTT TT...... (first 6 bytes)
        n = unpack_8(b'\x00\x00' + value[:6]) >> 6
        date = n >> 17 & D_MASK
        time = n & T_MASK

        # Extract S component from last 4 bytes
        n = unpack_4(value[-4:])
        if precision == 0b00:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSS0000
            nanosecond = (n >> 4 & MILLISECOND_MASK) * 1000000
            padding = n & 0b1111
        elif precision == 0b01:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSS00
            nanosecond = (n >> 2 & MICROSECOND_MASK) * 1000
            padding = n & 0b11
        elif precision == 0b10:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS
            nanosecond = n & NANOSECOND_MASK
        elif precision == 0b11:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TT000000
            padding = n & 0b111111

    elif type == 'DTSZ':
        # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
        # TTTTTTTT TTT..... (first 6 bytes)
        n = unpack_8(b'\x00\x00' + value[:6]) >> 5
        date = n >> 17 & D_MASK
        time = n & T_MASK

        # Extract S and Z components from last 5 bytes
        n = unpack_8(b'\x00\x00\x00' + value[-5:])
        if precision == 0b00:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSZZZ ZZZZ0000
            nanosecond = (n >> 11 & MILLISECOND_MASK) * 1000000
            tz_offset = n >> 4 & Z_MASK
            padding = n & 0b1111
        elif precision == 0b01:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSZ
            # ZZZZZZ00
            nanosecond = (n >> 9 & MICROSECOND_MASK) * 1000
            tz_offset = n >> 2 & Z_MASK
            padding = n & 0b11
        elif precision == 0b10:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS SZZZZZZZ
            nanosecond = n >> 7 & NANOSECOND_MASK
            tz_offset = n & Z_MASK
        elif precision == 0b11:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTZZZZZ ZZ000000
            tz_offset = n >> 6 & Z_MASK
            padding = n & 0b111111

    if padding:
        raise ValueError("padding bits must be zero")

    #
    # Split D and T components
    #

    if date is None:
        year = month = day = None
    else:
        year = date >> 9 & YEAR_MASK  # always within range
        if year == YEAR_EMPTY:
            year = None

        month = date >> 5 & MONTH_MASK
        if month == MONTH_EMPTY:
            month = None
        elif month > MONTH_MAX:
            raise ValueError("month not within supported range")
        else:
            month += 1

        day = date & DAY_MASK  # always within range
        if day == DAY_EMPTY:
            day = None
        else:
            day += 1

    if time is None:
        hour = minute = second = None
    else:
        hour = time >> 12 & HOUR_MASK
        if hour == HOUR_EMPTY:
            hour = None
        elif hour > HOUR_MAX:
            raise ValueError("hour not within supported range")

        minute = time >> 6 & MINUTE_MASK
        if minute == MINUTE_EMPTY:
            minute = None
        elif minute > MINUTE_MAX:
            raise ValueError("minute not within supported range")

        second = time & SECOND_MASK
        if second == SECOND_EMPTY:
            second = None
        elif second > SECOND_MAX:
            raise ValueError("second not within supported range")

    #
    # Normalize time zone offset
    #

    if tz_offset is not None:
        tz_offset = 15 * (tz_offset - 64)

    #
    # Sub-second fields are either all None, or none are None.
    #

    if nanosecond is not None and nanosecond > NANOSECOND_MAX:
        raise ValueError("sub-second precision not within supported range")

    return Moment(
        year, month, day,
        hour, minute, second, nanosecond,
        tz_offset)


def unpack(fp):
    """
    Unpack a *temporenc* value from a file-like object.

    This function consumes exactly the number of bytes required to
    unpack a single *temporenc* value.

    If no valid value could be read, this raises :py:exc:`ValueError`.

    :param file-like fp: readable file-like object
    :return: a parsed *temporenc* structure
    :rtype: :py:class:`Moment`
    """
    first = fp.read(1)
    _, _, size = _detect_type(ord(first))
    return unpackb(first + fp.read(size - 1))
