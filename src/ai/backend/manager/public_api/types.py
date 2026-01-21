from collections.abc import Mapping
from typing import TypeAlias

import aiohttp_cors

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
