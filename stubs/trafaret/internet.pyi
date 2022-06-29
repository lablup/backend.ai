from .base import OnError, WithRepr
from .regexp import Regexp, RegexpString

Email: WithRepr
URL: WithRepr
IPv4: WithRepr
IPv6: WithRepr
IP: WithRepr


class Hex(RegexpString): ...
class URLSafe(RegexpString): ...
