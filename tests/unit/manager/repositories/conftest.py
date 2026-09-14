from __future__ import annotations

# Register all models so SQLAlchemy's global configure_mappers() can resolve every
# row's string relationships regardless of which models a test shard happens to import.
from ai.backend.manager.models.base import ensure_all_tables_registered

ensure_all_tables_registered()
