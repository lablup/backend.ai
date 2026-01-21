import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import PosixPath

from dateutil.tz import gettz, tzutc

from ai.backend.common import msgpack
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import BinarySize, ResourceSlot, SlotTypes


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


def test_msgpack_uuid_as_map_key():
    device_id = uuid.uuid4()
    data = {device_id: 1234}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(next(iter(unpacked.keys())), uuid.UUID)
    assert unpacked[device_id] == 1234


def test_msgpack_uuid_to_str():
    device_id = uuid.uuid4()
    str_device_id = str(device_id)
    data = {device_id: 1234}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed, ext_hook_mapping=msgpack.uuid_to_str)
    assert isinstance(next(iter(unpacked.keys())), str)
    assert unpacked[str_device_id] == 1234


def test_msgpack_datetime():
    now = datetime.now(tzutc())
    data = {"timestamp": now}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    t = unpacked["timestamp"]
    assert isinstance(t, datetime)
    if t.tzinfo is not None:
        tzname = t.tzname()
        assert tzname is not None
        assert tzname.startswith("UTC")  # should be always UTC
    assert t == now

    now = datetime.now(gettz("Asia/Seoul"))
    data = {"timestamp": now}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    t = unpacked["timestamp"]
    assert isinstance(t, datetime)
    if t.tzinfo is not None:
        tzname = t.tzname()
        assert tzname is not None
        assert tzname.startswith("UTC")  # should be always UTC
    assert t == now


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
    assert isinstance(unpacked["size"], BinarySize)
    assert unpacked["size"] == 70368744177664

    size = BinarySize.from_str("Infinity")
    data = {"size": size}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["size"], Decimal)
    assert unpacked["size"] == Decimal("Infinity")


def test_msgpack_enum():
    value = SlotTypes.COUNT
    data = {"slot_type": value}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["slot_type"], SlotTypes)
    assert unpacked["slot_type"] == SlotTypes.COUNT


def test_msgpack_posixpath():
    path = PosixPath.cwd()
    # NOTE: In UNIX-like OS, pathlib.Path is also PosixPath
    data = {"path": path}
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)
    assert isinstance(unpacked["path"], PosixPath)
    assert unpacked["path"] == path


def test_msgpack_image_ref():
    imgref = ImageRef(
        name="python",
        project="lablup",
        tag="3.9-ubuntu20.04",
        registry="index.docker.io",
        architecture="x86_64",
        is_local=False,
    )
    packed = msgpack.packb(imgref)
    unpacked = msgpack.unpackb(packed)
    assert imgref == unpacked


def test_msgpack_resource_slot():
    resource_slot = ResourceSlot({"cpu": 1, "mem": 1024})
    packed = msgpack.packb(resource_slot)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == resource_slot

    resource_slot = ResourceSlot({"cpu": 2, "mem": Decimal(1024**5)})
    packed = msgpack.packb(resource_slot)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == resource_slot

    resource_slot = ResourceSlot({"cpu": 3, "mem": "1125899906842624"})
    packed = msgpack.packb(resource_slot)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == resource_slot
