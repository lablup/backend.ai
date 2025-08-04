from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
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
        default=0,
        description="""
        File size in bytes, 0 if size information is unavailable.
        Used for storage planning and transfer progress tracking.
        """,
        examples=[1024, 2048000, 0],
    )
    type: str = Field(
        default="file",
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


class ModelInfo(BaseModel):
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
    last_modified: Optional[datetime] = Field(
        default=None,
        description="""
        ISO timestamp when the model was last updated or modified.
        Indicates the freshness and maintenance status of the model.
        """,
    )
