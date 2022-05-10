from .base import Trafaret


class RegexpRaw(Trafaret):
    def __init__(self, regexp: str, re_flags: int = 0): ...

class Regexp(RegexpRaw): ...
