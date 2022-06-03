from ai.backend.common import msgpack


def test_msgpack_with_unicode():
    # msgpack-python module requires special treatment
    # to distinguish unicode strings and binary data
    # correctly, and ai.backend.common.msgpack wraps it for that.

    data = [b'\xff', '한글', 12345, 12.5]
    packed = msgpack.packb(data)
    unpacked = msgpack.unpackb(packed)

    # We also use tuples when unpacking for performance.
    assert unpacked == tuple(data)


def test_msgpack_kwargs():
    x = {'cpu': [0.42, 0.44], 'cuda_mem': [0.0, 0.0], 'cuda_util': [0.0, 0.0], 'mem': [30.0, 30.0]}
    packed = msgpack.packb(x)
    unpacked = msgpack.unpackb(packed, use_list=False)
    assert isinstance(unpacked['cpu'], tuple)
    assert isinstance(unpacked['mem'], tuple)
    assert isinstance(unpacked['cuda_mem'], tuple)
    assert isinstance(unpacked['cuda_util'], tuple)
    unpacked = msgpack.unpackb(packed, use_list=True)
    assert isinstance(unpacked['cpu'], list)
    assert isinstance(unpacked['mem'], list)
    assert isinstance(unpacked['cuda_mem'], list)
    assert isinstance(unpacked['cuda_util'], list)
