import uuid

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel


class VFolderIDPath(BaseRequestModel):
    vfolder_id: uuid.UUID = Field(validation_alias=AliasChoices("id", "vfolderId"))
