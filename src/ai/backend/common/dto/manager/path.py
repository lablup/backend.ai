import uuid

from pydantic import AliasChoices, BaseModel, Field


class VFolderIDPath(BaseModel):
    vfolder_id: uuid.UUID = Field(validation_alias=AliasChoices("vfolder_id", "vfolderId", "id"))
