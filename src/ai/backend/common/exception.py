from typing import Any, Mapping


class ConfigurationError(Exception):

    invalid_data: Mapping[str, Any]

    def __init__(self, invalid_data: Mapping[str, Any]) -> None:
        super().__init__(invalid_data)
        self.invalid_data = invalid_data


class UnknownImageReference(ValueError):
    '''
    Represents an error for invalid/unknown image reference.
    The first argument of this exception should be the reference given by the user.
    '''

    def __str__(self) -> str:
        return f'Unknown image reference: {self.args[0]}'


class ImageNotAvailable(ValueError):
    '''
    Represents an error for unavailability of the image in agents.
    The first argument of this exception should be the reference given by the user.
    '''

    def __str__(self) -> str:
        return f'Unavailable image in the agent: {self.args[0]}'


class UnknownImageRegistry(ValueError):
    '''
    Represents an error for invalid/unknown image registry.
    The first argument of this exception should be the registry given by the user.
    '''

    def __str__(self) -> str:
        return f'Unknown image registry: {self.args[0]}'


class AliasResolutionFailed(ValueError):
    '''
    Represents an alias resolution failure.
    The first argument of this exception should be the alias given by the user.
    '''

    def __str__(self) -> str:
        return f'Failed to resolve alias: {self.args[0]}'
