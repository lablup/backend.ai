"""Typed UUID identifiers for Backend.AI domain entities.

Each identifier lives in its own module. Import the specific type
directly from its module (``from ai.backend.common.identifier.image
import ImageID``) — this package deliberately does not re-export
types from ``__init__`` so that adding a new identifier does not
invalidate the type-check cache for unrelated consumers.
"""
