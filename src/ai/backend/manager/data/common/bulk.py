from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BulkCreateFailure:
    """A single failed item in a bulk create operation.

    Pure data carrier for data-layer bulk result types. Repositories convert
    their spec-carrying ``BulkCreatorError`` into this at the layer boundary, so
    the data layer never imports from repositories. Upper layers re-derive the
    failed item's identity from their original input via ``index``.
    """

    index: int
    exception: Exception


@dataclass(frozen=True)
class BulkUpdateFailure:
    """A single failed item in a bulk update operation.

    Data-layer counterpart of the repository's ``BulkUpdaterError``; see
    :class:`BulkCreateFailure` for the conversion contract.
    """

    index: int
    exception: Exception


@dataclass(frozen=True)
class BulkPurgeFailure:
    """A single failed item in a bulk purge operation.

    Data-layer counterpart of the repository's ``BulkPurgerError``; see
    :class:`BulkCreateFailure` for the conversion contract.
    """

    index: int
    exception: Exception
