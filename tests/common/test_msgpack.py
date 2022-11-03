import uuid
from datetime import datetime
from decimal import Decimal

from dateutil.tz import tzutc

from ai.backend.common import msgpack
from ai.backend.common.types import BinarySize


def test_msgpack_with_unicode():
    # msgpack-python module requires special treatment
    # to distinguish unicode strings and binary data
    # correctly, and ai.backend.common.msgpack wraps it for that.

    data = [b"\xff", "한글", 12345, 12.5]
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)

    # We also use tuples when unpacking for performance.
    assert unpacked == tuple(data)


def test_msgpack_kwargs():
    x = {"cpu": [0.42, 0.44], "cuda_mem": [0.0, 0.0], "cuda_util": [0.0, 0.0], "mem": [30.0, 30.0]}
    packed = msgpack.packb(x)
    unpacked = msgpack.unpackb(packed, use_list=False)
    assert isinstance(unpacked["cpu"], tuple)
    assert isinstance(unpacked["mem"], tuple)
    assert isinstance(unpacked["cuda_mem"], tuple)
    assert isinstance(unpacked["cuda_util"], tuple)
    unpacked = msgpack.unpackb(packed, use_list=True)
    assert isinstance(unpacked["cpu"], list)
    assert isinstance(unpacked["mem"], list)
    assert isinstance(unpacked["cuda_mem"], list)
    assert isinstance(unpacked["cuda_util"], list)


def test_msgpack_uuid():
    device_id = uuid.uuid4()
    data = {"device_id": device_id}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["device_id"], uuid.UUID)
    assert unpacked["device_id"] == device_id


def test_msgpack_datetime():
    now = datetime.now(tzutc())
    data = {"timestamp": now}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["timestamp"], datetime)
    assert unpacked["timestamp"] == now


def test_msgpack_decimal():
    value = Decimal(
        "1209705197565610203801239512319273475.2350976162030923750923750961028963490861246890575"
    )
    data = {"value": value}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["value"], Decimal)
    assert unpacked["value"] == value


def test_msgpack_binarysize():
    size = BinarySize.from_str("64T")
    data = {"size": size}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["size"], int)
    assert unpacked["size"] == size

    size = BinarySize.from_str("Infinity")
    data = {"size": size}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["size"], Decimal)
    assert unpacked["size"] == Decimal("Infinity")
