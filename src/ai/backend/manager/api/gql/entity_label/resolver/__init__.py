"""Label GQL resolvers."""

from .mutation import purge_entity_label, upsert_entity_label
from .query import entity_labels

__all__ = [
    "entity_labels",
    "upsert_entity_label",
    "purge_entity_label",
]
