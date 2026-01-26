from collections.abc import Mapping

import aiohttp_cors

type CORSOptions = Mapping[str, aiohttp_cors.ResourceOptions]
