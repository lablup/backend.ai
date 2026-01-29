class NoRocmDeviceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class GenericRocmError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class RocmUtilFetchError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class RocmMemFetchError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class LibraryError(RuntimeError):
    lib: str
    func: str
    code: int

    def __init__(self, lib: str, func: str, code: int) -> None:
        super().__init__(lib, func, code)
        self.lib = lib
        self.func = func
        self.code = code

    def __str__(self) -> str:
        return f"LibraryError: {self.lib}::{self.func}() returned error {self.code}"

    def __repr__(self) -> str:
        args = ", ".join(map(repr, self.args))
        return f"LibraryError({args})"
