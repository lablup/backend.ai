from ai.backend.client.session import AsyncSession


async def retrieve_all_files(
    client_session: AsyncSession, vfolder_name: str, path: str = ""
) -> set[str]:
    """
    Recursively retrieves all file paths in a virtual folder.
    """

    response = await client_session.VFolder(vfolder_name).list_files(path)
    assert "items" in response, "Response does not contain 'items' key."

    all_files = set()

    for item in response["items"]:
        if item["type"] == "FILE":
            file_path = f"{path}/{item['name']}" if path else item["name"]
            all_files.add(file_path)
        elif item["type"] == "DIRECTORY":
            subdir_path = f"{path}/{item['name']}" if path else item["name"]
            subdir_files = await retrieve_all_files(client_session, vfolder_name, subdir_path)
            all_files.update(subdir_files)

    return all_files
