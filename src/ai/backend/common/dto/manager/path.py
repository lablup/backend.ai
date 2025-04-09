import uuid

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class VFolderIDPath(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vfolder_id: uuid.UUID = Field(validation_alias=AliasChoices("vfolderId", "id"))
