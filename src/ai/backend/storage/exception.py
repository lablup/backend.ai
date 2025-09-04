from typing import Any, Optional

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotFound

from ai.backend.common.json import dump_json_str


class StorageProxyError(Exception):
    pass


class ExecutionError(StorageProxyError):
    pass


class ExternalError(StorageProxyError):
    pass


class NotEmptyError(StorageProxyError):
    pass


class VFolderCreationError(StorageProxyError):
    pass


class VFolderNotFoundError(StorageProxyError):
    pass


class QuotaScopeNotFoundError(StorageProxyError, HTTPNotFound):
    pass


class QuotaScopeAlreadyExists(StorageProxyError):
    pass


class InvalidQuotaConfig(StorageProxyError):
    pass


class InvalidSubpathError(StorageProxyError):
    pass


class InvalidQuotaScopeError(StorageProxyError):
    pass


class InvalidVolumeError(StorageProxyError):
    pass


class WatcherClientError(RuntimeError):
    pass


class InvalidAPIParameters(web.HTTPBadRequest):
    def __init__(
        self,
        type_suffix: str = "invalid-api-params",
        title: str = "Invalid API parameters",
        msg: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> None:
        payload = {
            "type": f"https://api.backend.ai/probs/storage/{type_suffix}",
            "title": title,
        }
        if msg is not None:
            payload["title"] = f"{title} ({msg})"
        if data is not None:
            payload["data"] = data
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class FileStreamUploadError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/file-stream-upload-failed",
            "title": "Failed to upload file stream",
        }
        if msg is not None:
            payload["title"] = f"Failed to upload file stream ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class FileStreamDownloadError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/file-stream-download-failed",
            "title": "Failed to download file stream",
        }
        if msg is not None:
            payload["title"] = f"Failed to download file stream ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class PresignedUploadURLGenerationError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/presigned-upload-url-generation-failed",
            "title": "Failed to generate presigned upload URL",
        }
        if msg is not None:
            payload["title"] = f"Failed to generate presigned upload URL ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class PresignedDownloadURLGenerationError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/presigned-download-url-generation-failed",
            "title": "Failed to generate presigned download URL",
        }
        if msg is not None:
            payload["title"] = f"Failed to generate presigned download URL ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class ObjectInfoFetchError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/object-info-fetch-failed",
            "title": "Failed to fetch object info",
        }
        if msg is not None:
            payload["title"] = f"Failed to fetch object info ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class StorageNotFoundError(web.HTTPNotFound):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/object-not-found",
            "title": "Storage Config Not Found",
        }
        if msg is not None:
            payload["title"] = f"Storage Config Not Found ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class StorageBucketNotFoundError(web.HTTPNotFound):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/bucket/object-not-found",
            "title": "Storage Bucket Not Found",
        }
        if msg is not None:
            payload["title"] = f"Storage Bucket Not Found ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class StorageBucketFileNotFoundError(web.HTTPNotFound):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/bucket/file/object-not-found",
            "title": "Storage Bucket File Not Found",
        }
        if msg is not None:
            payload["title"] = f"Storage Bucket File Not Found ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class RegistryNotFoundError(web.HTTPNotFound):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/registries/registry-not-found",
            "title": "Registry Not Found",
        }
        if msg is not None:
            payload["title"] = f"Registry Not Found ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class HuggingFaceAPIError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/registries/huggingface/api-error",
            "title": "HuggingFace API Error",
        }
        if msg is not None:
            payload["title"] = f"HuggingFace API Error ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class HuggingFaceModelNotFoundError(web.HTTPNotFound):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/registries/huggingface/model-not-found",
            "title": "HuggingFace Model Not Found",
        }
        if msg is not None:
            payload["title"] = f"HuggingFace Model Not Found ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class ObjectStorageConfigInvalidError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/object/config/invalid",
            "title": "Object Storage Config Invalid",
        }
        if msg is not None:
            payload["title"] = f"Object Storage Config Invalid ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class ReservoirStorageConfigInvalidError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/reservoir/config/invalid",
            "title": "Reservoir Storage Config Invalid",
        }
        if msg is not None:
            payload["title"] = f"Reservoir Storage Config Invalid ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class ArtifactStorageEmptyError(web.HTTPNotFound):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/artifact/config/invalid",
            "title": "Artifact Storage Empty",
        }
        if msg is not None:
            payload["title"] = f"Artifact Storage Empty ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )


class ArtifactRevisionEmptyError(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        payload = {
            "type": "https://api.backend.ai/probs/storage/artifact/revision/empty",
            "title": "Artifact Revision Empty",
        }
        if msg is not None:
            payload["title"] = f"Artifact Revision Empty ({msg})"
            payload["data"] = msg
        super().__init__(
            text=dump_json_str(payload),
            content_type="application/problem+json",
        )
