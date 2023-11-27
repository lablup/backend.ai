from .base import WithRepr
from .regexp import RegexpString

Email: WithRepr
URL: WithRepr
IPv4: WithRepr
IPv6: WithRepr
IP: WithRepr

class Hex(RegexpString): ...
class URLSafe(RegexpString): ...
