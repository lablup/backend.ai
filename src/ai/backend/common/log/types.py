import json
import zlib
from base64 import b64decode, b64encode
from dataclasses import dataclass
from enum import StrEnum


class ContainerLogType(StrEnum):
    ZLIB = "zlib"
    PLAINTEXT = "plaintext"


class ContainerLogError(Exception):
    """Exception Class for ContainerLog"""


@dataclass
class ContainerLogData:
    compress_type: ContainerLogType
    content: str  # base64 encoded

    @classmethod
    def from_log(cls, compress_type: ContainerLogType, log: bytes) -> "ContainerLogData":
        try:
            compressed = cls._compress(compress_type, log)
            encoded = cls._encode_base64(compressed)
            return cls(compress_type=compress_type, content=encoded)
        except Exception as e:
            raise ContainerLogError("Failed to encode or compress log") from e

    def get_content(self) -> bytes:
        try:
            decoded = self._decode_base64(self.content)
            return (
                self._decompress(decoded)
                if self.compress_type == ContainerLogType.ZLIB
                else decoded
            )
        except Exception as e:
            raise ContainerLogError("Failed to decode or decompress content") from e

    def serialize(self) -> bytes:
        try:
            payload = {
                "compress_type": self.compress_type.value,
                "content": self.content,
            }
            return json.dumps(payload).encode("utf-8")
        except Exception as e:
            raise ContainerLogError("Failed to serialize log data") from e

    @classmethod
    def deserialize(cls, data: bytes) -> "ContainerLogData":
        try:
            obj = json.loads(data.decode("utf-8"))
            return cls(compress_type=ContainerLogType(obj["compress_type"]), content=obj["content"])
        except Exception as e:
            raise ContainerLogError("Failed to deserialize log data") from e

    @staticmethod
    def _encode_base64(data: bytes) -> str:
        return b64encode(data).decode("utf-8")

    @staticmethod
    def _decode_base64(data: str) -> bytes:
        return b64decode(data)

    @staticmethod
    def _compress(compress_type: ContainerLogType, data: bytes) -> bytes:
        if compress_type == ContainerLogType.PLAINTEXT:
            return data

        if compress_type == ContainerLogType.ZLIB:
            return zlib.compress(data)

        raise ContainerLogError(f"Not Supported CompressedType : {compress_type}")

    @staticmethod
    def _decompress(data: bytes) -> bytes:
        return zlib.decompress(data)
