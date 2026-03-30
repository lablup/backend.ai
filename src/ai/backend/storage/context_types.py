from ai.backend.storage.plugin import AbstractArtifactVerifierPlugin


class ArtifactVerifierContext:
    _verifiers: dict[str, AbstractArtifactVerifierPlugin]

    def __init__(self) -> None:
        self._verifiers = {}

    def load_verifiers(self, verifiers: dict[str, AbstractArtifactVerifierPlugin]) -> None:
        self._verifiers.update(verifiers)
