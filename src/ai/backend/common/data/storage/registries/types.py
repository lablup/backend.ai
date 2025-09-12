import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.exception import ArtifactDefaultRevisionResolveError


class ModelSortKey(enum.StrEnum):
    LAST_MODIFIED = "last_modified"
    TRENDING_SCORE = "trending_score"
    CREATED_AT = "created_at"
    DOWNLOADS = "downloads"
    LIKES = "likes"


# TODO: Separate of the ModelTarget type used in the storage proxy and the one used in the manager
class ModelTarget(BaseModel):
    model_id: str = Field(
        description="""
        HuggingFace model ID to import.
        The model will be downloaded from HuggingFace Hub and stored in the specified storage.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2", "bert-base-uncased"],
    )
    revision: Optional[str] = Field(
        default=None,
        description="""
        Specific revision (branch or tag) of the model to import.
        Defaults to 'main' if not specified.
        """,
        examples=["main", "v1.0", "latest"],
    )

    def resolve_revision(self, registry_type: ArtifactRegistryType) -> str:
        if self.revision is not None:
            return self.revision

        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                return "main"
            case _:
                raise ArtifactDefaultRevisionResolveError(
                    f"Cannot resolve default revision for registry type: {registry_type}"
                )


class FileObjectData(BaseModel):
    """
    Model file information.
    """

    path: str = Field(
        description="""
        Relative path of the file within the model repository.
        This path is used to identify and locate files within the model structure.
        """,
        examples=["config.json", "pytorch_model.bin", "tokenizer/vocab.txt"],
    )
    size: int = Field(
        description="""
        File size in bytes, 0 if size information is unavailable.
        Used for storage planning and transfer progress tracking.
        """,
        examples=[1024, 2048000, 0],
    )
    type: str = Field(
        description="""
        Type of the file (e.g., 'file', 'directory', 'lfs').
        Indicates the nature of the file system object.
        """,
        examples=["file", "directory"],
    )
    download_url: str = Field(
        description="""
        Direct HTTP URL for downloading the file.
        This URL can be used to directly download the file from HuggingFace Hub.
        """,
        examples=["https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"],
    )


class ModelData(BaseModel):
    """
    Model Artifact information.
    """

    id: str = Field(
        description="""
        Unique identifier for the model (e.g., 'microsoft/DialoGPT-medium').
        This follows the HuggingFace Hub naming convention of organization/model-name.
        """,
        examples=["microsoft/DialoGPT-medium", "openai/gpt-2", "bert-base-uncased"],
    )
    name: str = Field(
        description="""
        Display name of the model, typically the last part of the model ID.
        Used for human-readable identification of the model.
        """,
        examples=["DialoGPT-medium", "gpt-2", "bert-base-uncased"],
    )
    author: Optional[str] = Field(
        default=None,
        description="""
        Username or organization that owns the model repository.
        Extracted from the model ID or provided by the HuggingFace Hub API.
        """,
        examples=["microsoft", "openai", None],
    )
    revision: str = Field(
        default="main",
        description="""
        Git revision (branch, tag, or commit hash) of the model.
        Specifies which version of the model to use.
        """,
        examples=["main", "v1.0", "7b2f134a", "dev"],
    )
    tags: list[str] = Field(
        default_factory=list,
        description="""
        List of tags describing the model's characteristics, frameworks, and use cases.
        These tags help categorize and discover models on HuggingFace Hub.
        """,
        examples=[["pytorch", "text-generation"], ["transformers", "image-classification"]],
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="""
        ISO timestamp when the model repository was created.
        Provides information about the model's age and development timeline.
        """,
    )
    modified_at: Optional[datetime] = Field(
        default=None,
        description="""
        ISO timestamp when the model was last updated or modified.
        Indicates the freshness and maintenance status of the model.
        """,
    )
    readme: Optional[str] = Field(
        default=None,
        description="""
        README file content for the model.
        Provides documentation and usage instructions for the model.
        """,
    )
    size: Optional[int] = Field(
        default=None,
        description="""
        Total size of the model repository in bytes, if available.
        Helps in assessing storage requirements and download times.
        """,
        examples=[2048000, 512000000],
    )
