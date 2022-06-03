class InitializationError(Exception):
    """
    Errors during agent initialization and compute plugin setup
    """
    pass


class ResourceError(ValueError):
    pass


class UnsupportedResource(ResourceError):
    pass


class InvalidResourceCombination(ResourceError):
    pass


class InvalidResourceArgument(ResourceError):
    pass


class NotMultipleOfQuantum(InvalidResourceArgument):
    pass


class InsufficientResource(ResourceError):
    pass


class UnsupportedBaseDistroError(RuntimeError):
    pass


class K8sError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class AgentError(RuntimeError):
    '''
    A dummy exception class to distinguish agent-side errors passed via
    aiozmq.rpc calls.

    It carrise two args tuple: the exception type and exception arguments from
    the agent.
    '''

    def __init__(self, *args, exc_repr: str = None):
        super().__init__(*args)
        self.exc_repr = exc_repr
