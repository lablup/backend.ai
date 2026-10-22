from collections.abc import Mapping

from ai.backend.kernel.interpolation.base import BaseServiceInterpolator
from ai.backend.kernel.interpolation.delimiter import DelimiterInterpolator
from ai.backend.kernel.interpolation.legacy import LegacyInterpolator
from ai.backend.kernel.interpolation.types import InterpolationMode

INTERPOLATORS: Mapping[InterpolationMode, BaseServiceInterpolator] = {
    InterpolationMode.LEGACY: LegacyInterpolator(),
    InterpolationMode.DELIMITER: DelimiterInterpolator(),
}
