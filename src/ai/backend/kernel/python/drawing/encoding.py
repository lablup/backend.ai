import base64

import msgpack


def encode_commands(cmdlist):
    bindata = msgpack.packb(cmdlist, use_bin_type=True)
    return base64.b64encode(bindata).decode("ascii")


def decode_commands(data):
    bindata = base64.b64decode(data)
    return msgpack.unpackb(bindata, raw=False)
