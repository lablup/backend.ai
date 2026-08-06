class BrokerUnreachable(Exception):
    pass


class ReleaseDenied(Exception):
    pass


class EmptySecret(Exception):
    pass


class PolicyError(Exception):
    pass


class ClockUntrusted(Exception):
    pass


class DecisionLogNotDurable(Exception):
    pass
