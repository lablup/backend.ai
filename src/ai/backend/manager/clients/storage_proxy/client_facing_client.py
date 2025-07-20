from ai.backend.manager.clients.storage_proxy.base import StorageProxyHTTPClient


class StorageProxyClientFacingClient:
    """
    Client for interacting with the storage proxy, specifically for virtual folder operations.
    This client handles various HTTP status codes and raises appropriate exceptions.
    """

    _client: StorageProxyHTTPClient

    def __init__(self, client: StorageProxyHTTPClient):
        self._client = client
