import re
from dataclasses import dataclass
from datetime import timedelta

LEAF_LIFETIME = timedelta(days=7)
RENEWAL_INTERVAL = timedelta(days=1)
CLOCK_SKEW_ALLOWANCE = timedelta(minutes=5)

_LABEL = re.compile(r"\A[a-z0-9][a-z0-9._-]{0,62}\Z")
_DNS_NAME = re.compile(r"\A[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*\Z")


class PKIError(Exception):
    pass


class IdentityRefused(PKIError):
    pass


class IssuanceRefused(PKIError):
    pass


@dataclass(frozen=True)
class WorkloadIdentity:
    trust_domain: str
    role: str
    instance: str
    dns_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in (self.trust_domain, self.role, self.instance):
            if not _LABEL.match(field):
                raise IdentityRefused(f"malformed identity component: {field!r}")
        for name in self.dns_names:
            if not _DNS_NAME.match(name):
                raise IdentityRefused(f"malformed dns name: {name!r}")

    @property
    def uri(self) -> str:
        return f"spiffe://{self.trust_domain}/{self.role}/{self.instance}"

    @property
    def common_name(self) -> str:
        return self.dns_names[0] if self.dns_names else f"{self.role}.{self.instance}"
