from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import os
import pathlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePosixPath
from types import ModuleType
from typing import IO, Final, Protocol, cast, override

FORMAT_ID: Final = "backend.ai/cc-storage/v1"
CAPABILITY_HEADER: Final = "X-BackendAI-Storage-Format"
CONCURRENT_TIER: Final = "concurrent"
INTEGRITY_TIER: Final = "integrity"
TIERS: Final = (CONCURRENT_TIER, INTEGRITY_TIER)
TAMPER_EVIDENT: Final = {CONCURRENT_TIER: False, INTEGRITY_TIER: True}
TIER_DISCLOSURE: Final = {
    CONCURRENT_TIER: (
        "Content and names are encrypted against the storage operator. Modification of any stored"
        " byte, frame reordering, truncation and extension are detected on read. Deletion of a whole"
        " file, rollback of a whole file to an earlier version, and the shape of the tree are not"
        " detected."
    ),
    INTEGRITY_TIER: (
        "Content and names are encrypted and the folder is tamper-evident under an exclusive mount"
        " lease, so only one session may hold it at a time."
    ),
}


class StorageFormatUnavailable(RuntimeError):
    pass


class FolderRootVectorMissing(RuntimeError):
    pass


@lru_cache(maxsize=1)
def extension() -> ModuleType:
    try:
        return importlib.import_module("bai_storage_format")
    except ImportError:
        pass
    candidates: list[pathlib.Path] = []
    override = os.environ.get("BACKENDAI_STORAGE_FORMAT_LIB")
    if override:
        candidates.append(pathlib.Path(override))
    built = pathlib.Path(__file__).resolve().parents[4] / "rust" / "target"
    candidates += [
        built / profile / f"libbai_storage_format.{suffix}"
        for profile in ("release", "debug")
        for suffix in ("dylib", "so")
    ]
    for path in candidates:
        if not path.exists():
            continue
        loader = importlib.machinery.ExtensionFileLoader("bai_storage_format", str(path))
        spec = importlib.util.spec_from_loader("bai_storage_format", loader)
        if spec is None:
            continue
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module
    raise StorageFormatUnavailable(f"no build of {FORMAT_ID} is importable")


class EncryptedName(Protocol):
    @property
    def on_disk(self) -> str: ...

    @property
    def encoded(self) -> str: ...

    @property
    def sidecar_name(self) -> str | None: ...

    @property
    def sidecar_content(self) -> str | None: ...


@dataclass(frozen=True)
class FolderKeyMaterial:
    key: bytes
    tier: str = CONCURRENT_TIER

    @classmethod
    def from_json(cls, payload: dict[str, str]) -> FolderKeyMaterial:
        return cls(
            key=bytes.fromhex(payload["key"]),
            tier=payload.get("tier", CONCURRENT_TIER),
        )

    def to_json(self) -> dict[str, str]:
        return {
            "key": self.key.hex(),
            "tier": self.tier,
        }


def stored_len(plaintext_len: int) -> int:
    return int(extension().stored_len(plaintext_len))


class FolderCipher:
    def __init__(self, material: FolderKeyMaterial) -> None:
        self.fmt = extension()
        self.material = material
        self._key = self.fmt.FolderKey(material.key)

    def seal(self, plaintext: bytes) -> bytes:
        return bytes(self._key.encrypt(plaintext))

    def open(self, stored: bytes) -> bytes:
        return bytes(self._key.decrypt(stored))

    def name(self, dir_iv: bytes, name: str) -> EncryptedName:
        return cast(EncryptedName, self._key.encrypt_name(dir_iv, name))

    def plain_name(self, dir_iv: bytes, encoded: str) -> str:
        return str(self._key.decrypt_name(dir_iv, encoded))


class EncryptingReader(io.RawIOBase):
    def __init__(self, source: IO[bytes], cipher: FolderCipher, plaintext_size: int) -> None:
        fmt = cipher.fmt
        self._fmt = fmt
        self._source = source
        self._key = cipher._key
        self._file_id = fmt.new_file_id()
        self._header = self._key.file_header(self._file_id)
        self._plain = plaintext_size
        self._size = int(fmt.stored_len(plaintext_size))
        self._count = int(fmt.chunk_count(plaintext_size))
        self._nonces: dict[int, bytes] = {}
        self._held = -1
        self._frame = b""
        self._pos = 0

    @property
    def stored_size(self) -> int:
        return self._size

    @override
    def readable(self) -> bool:
        return True

    @override
    def seekable(self) -> bool:
        return True

    @override
    def tell(self) -> int:
        return self._pos

    @override
    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        origin = {os.SEEK_SET: 0, os.SEEK_CUR: self._pos, os.SEEK_END: self._size}[whence]
        self._pos = max(0, min(self._size, origin + offset))
        return self._pos

    @override
    def close(self) -> None:
        self._source.close()
        super().close()

    def _frame_at(self, index: int) -> bytes:
        if index != self._held:
            start = index * self._fmt.CHUNK_PLAINTEXT
            self._source.seek(start)
            plain = self._source.read(min(self._fmt.CHUNK_PLAINTEXT, self._plain - start))
            nonce = self._nonces.setdefault(index, os.urandom(self._fmt.NONCE_LEN))
            self._frame = self._key.seal_chunk(
                self._file_id, index, index + 1 == self._count, nonce, plain
            )
            self._held = index
        return self._frame

    @override
    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self._size - self._pos
        out = bytearray()
        while size > 0 and self._pos < self._size:
            if self._pos < self._fmt.HEADER_LEN:
                piece = self._header[self._pos : self._fmt.HEADER_LEN]
            else:
                offset = self._pos - self._fmt.HEADER_LEN
                piece = self._frame_at(offset // self._fmt.CHUNK_STORED)[
                    offset % self._fmt.CHUNK_STORED :
                ]
            piece = piece[:size]
            out += piece
            self._pos += len(piece)
            size -= len(piece)
        return bytes(out)


def decrypt_file(cipher: FolderCipher, source: pathlib.Path, target: pathlib.Path) -> None:
    fmt = cipher.fmt
    count = fmt.chunk_count(fmt.plaintext_len(source.stat().st_size))
    with source.open("rb") as src, target.open("wb") as dst:
        file_id = fmt.parse_header(src.read(fmt.HEADER_LEN + fmt.NONCE_LEN + fmt.TAG_LEN))
        src.seek(fmt.HEADER_LEN)
        for index in range(count):
            dst.write(
                cipher._key.open_chunk(
                    file_id, index, index + 1 == count, src.read(fmt.CHUNK_STORED)
                )
            )


class CipherStore(Protocol):
    async def read(self, path: str) -> bytes: ...

    async def write(self, path: str, data: bytes) -> None: ...

    async def mkdir(self, path: str) -> None: ...

    async def listdir(self, path: str) -> list[tuple[str, int, bool]]: ...


@dataclass(frozen=True)
class CipherEntry:
    name: str
    on_disk: str
    size: int
    is_dir: bool


def _join(parent: str, child: str) -> str:
    return f"{parent}/{child}" if parent else child


def _components(relpath: str | os.PathLike[str]) -> list[str]:
    return [part for part in PurePosixPath(str(relpath)).parts if part not in (".", "/", "")]


class CipherPaths:
    def __init__(self, cipher: FolderCipher, store: CipherStore) -> None:
        self.cipher = cipher
        self._store = store
        self._ivs: dict[str, bytes] = {}

    async def _sealed(self, cipher_dir: str) -> list[tuple[str, int, bool]]:
        fmt = self.cipher.fmt
        return [
            entry
            for entry in await self._store.listdir(cipher_dir)
            if not fmt.is_reserved(entry[0])
        ]

    async def dir_iv(self, cipher_dir: str, *, create: bool) -> bytes:
        if cipher_dir in self._ivs:
            return self._ivs[cipher_dir]
        fmt = self.cipher.fmt
        marker = _join(cipher_dir, fmt.DIR_IV_FILE)
        try:
            iv = await self._store.read(marker)
        except FileNotFoundError:
            if not cipher_dir and await self._sealed(cipher_dir):
                raise FolderRootVectorMissing(
                    f"the ciphertext root holds sealed entries but no {fmt.DIR_IV_FILE}; this"
                    " folder was written before the vector of its root directory was carried on"
                    " the export, and no key releasable today decrypts the names in it"
                ) from None
            if not create:
                raise
            await self._store.mkdir(cipher_dir)
            await self._store.write(marker, fmt.new_dir_iv())
            iv = await self._store.read(marker)
        self._ivs[cipher_dir] = iv
        return iv

    async def resolve(self, relpath: str | os.PathLike[str], *, create: bool = False) -> str:
        current = ""
        for part in _components(relpath):
            encrypted = self.cipher.name(await self.dir_iv(current, create=create), part)
            sidecar, content = encrypted.sidecar_name, encrypted.sidecar_content
            if create and sidecar is not None and content is not None:
                await self._store.write(_join(current, sidecar), content.encode("ascii"))
            current = _join(current, encrypted.on_disk)
        return current

    async def listing(self, relpath: str | os.PathLike[str]) -> list[CipherEntry]:
        fmt = self.cipher.fmt
        cipher_dir = await self.resolve(relpath)
        sealed = await self._sealed(cipher_dir)
        if not sealed:
            return []
        iv = await self.dir_iv(cipher_dir, create=False)
        entries: list[CipherEntry] = []
        for on_disk, size, is_dir in sealed:
            sidecar = fmt.sidecar_of(on_disk)
            try:
                encoded = (
                    (await self._store.read(_join(cipher_dir, sidecar))).decode("ascii")
                    if sidecar is not None
                    else on_disk
                )
                name = self.cipher.plain_name(iv, encoded)
            except (ValueError, UnicodeDecodeError, FileNotFoundError):
                continue
            entries.append(
                CipherEntry(
                    name=name,
                    on_disk=on_disk,
                    size=size if is_dir else fmt.plaintext_len(size),
                    is_dir=is_dir,
                )
            )
        return entries
