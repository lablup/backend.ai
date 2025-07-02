import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VFolderMeta:
    id: uuid.UUID
    name: str


@dataclass
class UploadedFile:
    path: str
    content: str


@dataclass
class UploadedFilesMeta:
    files: list[UploadedFile]
    uploaded_path: Path


@dataclass
class VFolderInvitationMeta:
    invited_user_emails: list[str]
