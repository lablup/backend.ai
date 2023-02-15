import enum

class StringSetFlag(enum.Flag):
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __or__(  # type: ignore[override]
        self,
        other: StringSetFlag | str | set[str] | frozenset[str],
    ) -> set[str]: ...
    def __and__(  # type: ignore[override]
        self,
        other: StringSetFlag | str | set[str] | frozenset[str],
    ) -> bool: ...
    def __xor__(  # type: ignore[override]
        self,
        other: StringSetFlag | str | set[str] | frozenset[str],
    ) -> set[str]: ...
    def __ror__(  # type: ignore[override]
        self,
        other: StringSetFlag | str | set[str] | frozenset[str],
    ) -> set[str]: ...
    def __rand__(  # type: ignore[override]
        self,
        other: StringSetFlag | str | set[str] | frozenset[str],
    ) -> bool: ...
    def __rxor__(  # type: ignore[override]
        self,
        other: StringSetFlag | str | set[str] | frozenset[str],
    ) -> set[str]: ...
    def __str__(self) -> str: ...
