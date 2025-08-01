from typing import Optional

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """HuggingFace model file information."""

    path: str = Field(..., description="Relative path of the file within the model repository")
    size: int = Field(
        default=0, description="File size in bytes, 0 if size information is unavailable"
    )
    type: str = Field(
        default="file", description="Type of the file (e.g., 'file', 'directory', 'lfs')"
    )
    download_url: str = Field(..., description="Direct HTTP URL for downloading the file")
    error: Optional[str] = Field(
        default=None, description="Error message encountered while retrieving file information"
    )

    @property
    def size_mb(self) -> float:
        """Return file size in MB."""
        return self.size / (1024 * 1024) if self.size > 0 else 0.0

    @property
    def size_display(self) -> str:
        """Return user-friendly size display."""
        if self.size == 0:
            return "(size info unavailable)"
        return f"({self.size_mb:.1f} MB)"


class ModelInfo(BaseModel):
    """HuggingFace model information."""

    id: str = Field(
        ..., description="Unique identifier for the model (e.g., 'microsoft/DialoGPT-medium')"
    )
    name: str = Field(
        ..., description="Display name of the model, typically the last part of the model ID"
    )
    author: Optional[str] = Field(
        default=None, description="Username or organization that owns the model repository"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of tags describing the model's characteristics, frameworks, and use cases",
    )
    pipeline_tag: Optional[str] = Field(
        default=None,
        description="Primary ML pipeline task this model is designed for (e.g., 'text-generation', 'image-classification')",
    )
    downloads: int = Field(
        default=0,
        description="Total number of times this model has been downloaded from HuggingFace Hub",
    )
    likes: int = Field(
        default=0,
        description="Number of users who have liked/starred this model on HuggingFace Hub",
    )
    created_at: str = Field(
        default="", description="ISO timestamp when the model repository was created"
    )
    last_modified: str = Field(
        default="", description="ISO timestamp when the model was last updated or modified"
    )
    files: list[FileInfo] = Field(
        default_factory=list,
        description="Complete list of all files contained within the model repository",
    )

    def get_display_tags(self, limit: int = 5) -> str:
        """Return first N tags as comma-separated string."""
        return ", ".join(self.tags[:limit])

    @property
    def file_count(self) -> int:
        """Return number of files."""
        return len(self.files)


class HuggingFaceFileData(BaseModel):
    """HuggingFace model file information."""

    path: str = Field(..., description="Relative path of the file within the model repository")
    size: int = Field(
        default=0, description="File size in bytes, 0 if size information is unavailable"
    )
    type: str = Field(
        default="file", description="Type of the file (e.g., 'file', 'directory', 'lfs')"
    )
    download_url: str = Field(..., description="Direct HTTP URL for downloading the file")
    error: Optional[str] = Field(
        default=None, description="Error message encountered while retrieving file information"
    )


class HuggingFaceModelInfo(BaseModel):
    """HuggingFace model information."""

    id: str = Field(
        ..., description="Unique identifier for the model (e.g., 'microsoft/DialoGPT-medium')"
    )
    name: str = Field(
        ..., description="Display name of the model, typically the last part of the model ID"
    )
    author: Optional[str] = Field(
        default=None, description="Username or organization that owns the model repository"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of tags describing the model's characteristics, frameworks, and use cases",
    )
    pipeline_tag: Optional[str] = Field(
        default=None,
        description="Primary ML pipeline task this model is designed for (e.g., 'text-generation', 'image-classification')",
    )
    downloads: int = Field(
        default=0,
        description="Total number of times this model has been downloaded from HuggingFace Hub",
    )
    likes: int = Field(
        default=0,
        description="Number of users who have liked/starred this model on HuggingFace Hub",
    )
    created_at: str = Field(
        default="", description="ISO timestamp when the model repository was created"
    )
    last_modified: str = Field(
        default="", description="ISO timestamp when the model was last updated or modified"
    )
    files: list[HuggingFaceFileData] = Field(
        default_factory=list,
        description="Complete list of all files contained within the model repository",
    )
