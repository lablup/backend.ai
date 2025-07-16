from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for metric repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.METRIC)


class MetricRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
