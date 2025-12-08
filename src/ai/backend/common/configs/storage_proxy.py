from __future__ import annotations

from typing import Optional

from aiohttp import ClientTimeout
from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema


class TimeoutConfig(BaseConfigSchema):
    """
    Timeout configuration for a single HTTP request.
    All fields are optional; None means no timeout for that particular setting.
    """

    total: Optional[float] = Field(
        default=None,
        description="""
        Total timeout for the entire request (in seconds).
        None means no timeout.
        """,
        examples=[300.0],
    )
    connect: Optional[float] = Field(
        default=None,
        description="""
        Timeout for acquiring a connection from the pool (in seconds).
        None means no timeout.
        """,
        examples=[60.0],
    )
    sock_connect: Optional[float] = Field(
        default=None,
        description="""
        Timeout for connecting to a peer for a new connection (in seconds).
        None means no timeout.
        """,
        examples=[30.0],
        validation_alias=AliasChoices("sock-connect", "sock_connect"),
        serialization_alias="sock-connect",
    )
    sock_read: Optional[float] = Field(
        default=None,
        description="""
        Timeout for reading a portion of data from a peer (in seconds).
        None means no timeout.
        """,
        examples=[300.0],
        validation_alias=AliasChoices("sock-read", "sock_read"),
        serialization_alias="sock-read",
    )

    def to_client_timeout(self) -> ClientTimeout:
        return ClientTimeout(
            total=self.total,
            connect=self.connect,
            sock_connect=self.sock_connect,
            sock_read=self.sock_read,
        )


_DEFAULT_TIMEOUT = TimeoutConfig(total=300.0, sock_connect=30.0)


class StorageProxyTimeoutConfig(BaseConfigSchema):
    """
    Per-method timeout configuration for StorageProxyManagerFacingClient.
    Each field corresponds to a method in the client class.
    If not specified, the default timeout (total=300s, sock_connect=30s) is used.
    """

    # Volume operations
    get_volumes: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_volumes operation.",
        validation_alias=AliasChoices("get-volumes", "get_volumes"),
        serialization_alias="get-volumes",
    )

    # Folder operations
    create_folder: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for create_folder operation.",
        validation_alias=AliasChoices("create-folder", "create_folder"),
        serialization_alias="create-folder",
    )
    delete_folder: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for delete_folder operation.",
        validation_alias=AliasChoices("delete-folder", "delete_folder"),
        serialization_alias="delete-folder",
    )
    clone_folder: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for clone_folder operation.",
        validation_alias=AliasChoices("clone-folder", "clone_folder"),
        serialization_alias="clone-folder",
    )
    get_mount_path: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_mount_path operation.",
        validation_alias=AliasChoices("get-mount-path", "get_mount_path"),
        serialization_alias="get-mount-path",
    )

    # Volume info operations
    get_volume_hwinfo: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_volume_hwinfo operation.",
        validation_alias=AliasChoices("get-volume-hwinfo", "get_volume_hwinfo"),
        serialization_alias="get-volume-hwinfo",
    )
    get_volume_performance_metric: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_volume_performance_metric operation.",
        validation_alias=AliasChoices(
            "get-volume-performance-metric", "get_volume_performance_metric"
        ),
        serialization_alias="get-volume-performance-metric",
    )
    get_fs_usage: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_fs_usage operation.",
        validation_alias=AliasChoices("get-fs-usage", "get_fs_usage"),
        serialization_alias="get-fs-usage",
    )

    # Quota operations
    get_volume_quota: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_volume_quota operation.",
        validation_alias=AliasChoices("get-volume-quota", "get_volume_quota"),
        serialization_alias="get-volume-quota",
    )
    update_volume_quota: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for update_volume_quota operation.",
        validation_alias=AliasChoices("update-volume-quota", "update_volume_quota"),
        serialization_alias="update-volume-quota",
    )
    get_quota_scope: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_quota_scope operation.",
        validation_alias=AliasChoices("get-quota-scope", "get_quota_scope"),
        serialization_alias="get-quota-scope",
    )
    update_quota_scope: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for update_quota_scope operation.",
        validation_alias=AliasChoices("update-quota-scope", "update_quota_scope"),
        serialization_alias="update-quota-scope",
    )
    delete_quota_scope_quota: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for delete_quota_scope_quota operation.",
        validation_alias=AliasChoices("delete-quota-scope-quota", "delete_quota_scope_quota"),
        serialization_alias="delete-quota-scope-quota",
    )

    # File operations
    mkdir: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for mkdir operation.",
    )
    rename_file: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for rename_file operation.",
        validation_alias=AliasChoices("rename-file", "rename_file"),
        serialization_alias="rename-file",
    )
    delete_files: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for delete_files operation.",
        validation_alias=AliasChoices("delete-files", "delete_files"),
        serialization_alias="delete-files",
    )
    delete_files_async: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for delete_files_async operation.",
        validation_alias=AliasChoices("delete-files-async", "delete_files_async"),
        serialization_alias="delete-files-async",
    )
    move_file: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for move_file operation.",
        validation_alias=AliasChoices("move-file", "move_file"),
        serialization_alias="move-file",
    )
    upload_file: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for upload_file operation.",
        validation_alias=AliasChoices("upload-file", "upload_file"),
        serialization_alias="upload-file",
    )
    download_file: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for download_file operation.",
        validation_alias=AliasChoices("download-file", "download_file"),
        serialization_alias="download-file",
    )
    list_files: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for list_files operation.",
        validation_alias=AliasChoices("list-files", "list_files"),
        serialization_alias="list-files",
    )
    fetch_file: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for fetch_file operation.",
        validation_alias=AliasChoices("fetch-file", "fetch_file"),
        serialization_alias="fetch-file",
    )

    # Folder usage operations
    get_folder_usage: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_folder_usage operation.",
        validation_alias=AliasChoices("get-folder-usage", "get_folder_usage"),
        serialization_alias="get-folder-usage",
    )
    get_used_bytes: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_used_bytes operation.",
        validation_alias=AliasChoices("get-used-bytes", "get_used_bytes"),
        serialization_alias="get-used-bytes",
    )

    # HuggingFace operations
    scan_huggingface_models: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for scan_huggingface_models operation.",
        validation_alias=AliasChoices("scan-huggingface-models", "scan_huggingface_models"),
        serialization_alias="scan-huggingface-models",
    )
    retrieve_huggingface_models: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for retrieve_huggingface_models operation.",
        validation_alias=AliasChoices("retrieve-huggingface-models", "retrieve_huggingface_models"),
        serialization_alias="retrieve-huggingface-models",
    )
    retrieve_huggingface_model: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for retrieve_huggingface_model operation.",
        validation_alias=AliasChoices("retrieve-huggingface-model", "retrieve_huggingface_model"),
        serialization_alias="retrieve-huggingface-model",
    )
    import_huggingface_models: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for import_huggingface_models operation.",
        validation_alias=AliasChoices("import-huggingface-models", "import_huggingface_models"),
        serialization_alias="import-huggingface-models",
    )
    get_huggingface_model_commit_hash: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_huggingface_model_commit_hash operation.",
        validation_alias=AliasChoices(
            "get-huggingface-model-commit-hash", "get_huggingface_model_commit_hash"
        ),
        serialization_alias="get-huggingface-model-commit-hash",
    )

    # Reservoir operations
    import_reservoir_models: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for import_reservoir_models operation.",
        validation_alias=AliasChoices("import-reservoir-models", "import_reservoir_models"),
        serialization_alias="import-reservoir-models",
    )

    # S3 operations
    download_s3_file: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for download_s3_file operation.",
        validation_alias=AliasChoices("download-s3-file", "download_s3_file"),
        serialization_alias="download-s3-file",
    )
    get_s3_presigned_download_url: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_s3_presigned_download_url operation.",
        validation_alias=AliasChoices(
            "get-s3-presigned-download-url", "get_s3_presigned_download_url"
        ),
        serialization_alias="get-s3-presigned-download-url",
    )
    get_s3_presigned_upload_url: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for get_s3_presigned_upload_url operation.",
        validation_alias=AliasChoices("get-s3-presigned-upload-url", "get_s3_presigned_upload_url"),
        serialization_alias="get-s3-presigned-upload-url",
    )
    delete_s3_object: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for delete_s3_object operation.",
        validation_alias=AliasChoices("delete-s3-object", "delete_s3_object"),
        serialization_alias="delete-s3-object",
    )

    # VFS operations
    download_vfs_file_streaming: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for download_vfs_file_streaming operation.",
        validation_alias=AliasChoices("download-vfs-file-streaming", "download_vfs_file_streaming"),
        serialization_alias="download-vfs-file-streaming",
    )
    list_vfs_files: TimeoutConfig = Field(
        default_factory=lambda: _DEFAULT_TIMEOUT,
        description="Timeout for list_vfs_files operation.",
        validation_alias=AliasChoices("list-vfs-files", "list_vfs_files"),
        serialization_alias="list-vfs-files",
    )
