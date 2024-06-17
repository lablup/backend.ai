import json
import os
from contextlib import closing
from io import TextIOWrapper

import pytest

from ...utils.cli import EOF, ClientRunnerFunc


@pytest.mark.dependency()
def test_create_vfolder(run_user: ClientRunnerFunc):
    """
    Test create vfolder function.
    This test should be executed first in test_vfolder.py.
    TODO: Unannotate the following code after group deletion issue is resolved.
    """
    # Create group first
    # with closing(run(['admin', 'group', 'add', 'default', 'testgroup'])) as p:
    #     p.expect(EOF)
    #     assert 'Group name testgroup is created in domain default' in p.before.decode(), \
    #         'Test group not created successfully.'
    print("[ Create vfolder ]")
    # Create vfolder
    with closing(run_user(["vfolder", "create", "-p", "rw", "test_folder1", "local:volume1"])) as p:
        p.expect(EOF)
        assert (
            'Virtual folder "test_folder1" is created' in p.before.decode()
        ), "Test folder1 not created successfully."

    with closing(run_user(["vfolder", "create", "-p", "ro", "test_folder2", "local:volume1"])) as p:
        p.expect(EOF)
        assert (
            'Virtual folder "test_folder2" is created' in p.before.decode()
        ), "Test folder2 not created successfully."

    # Check if vfolder is created
    with closing(run_user(["--output=json", "vfolder", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        folder_list = loaded.get("items")
        assert isinstance(folder_list, list), "Error in listing test folders!"

    test_folder1 = get_folder_from_list(folder_list, "test_folder1")
    test_folder2 = get_folder_from_list(folder_list, "test_folder2")

    assert bool(test_folder1), "Test folder 1 doesn't exist!"
    assert test_folder1.get("permission") == "rw", "Test folder 1 permission mismatch."

    assert bool(test_folder2), "Test folder 2 doesn't exist!"
    assert test_folder2.get("permission") == "ro", "Test folder 2 permission mismatch."


@pytest.mark.dependency(depends=["test_create_vfolder"])
def test_rename_vfolder(run_user: ClientRunnerFunc):
    """
    Test rename vfolder function.
    !! Make sure you execute this test after test_create_vfolder !!
    Otherwise, it will raise an error.
    """
    print("[ Rename vfolder ]")
    # Rename vfolder
    with closing(run_user(["vfolder", "rename", "test_folder1", "test_folder3"])) as p:
        p.expect(EOF)
        assert "Renamed" in p.before.decode(), "Test folder1 not renamed successfully."

    # Check if vfolder is updated
    with closing(run_user(["--output=json", "vfolder", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        folder_list = loaded.get("items")
        assert isinstance(folder_list, list), "Error in listing test folders!"

    test_folder3 = get_folder_from_list(folder_list, "test_folder3")
    assert bool(test_folder3), "Test folder 3 doesn't exist!"


@pytest.mark.dependency(depends=["test_create_vfolder"])
def test_upload_file(run_user: ClientRunnerFunc, txt_file: TextIOWrapper):
    """
    Test for uploading a file to the vfolder.
    !! Make sure you execute this test after test_create_vfolder !!
    Otherwise, it will raise an error.
    """

    vfolder_name = "test_folder2"
    file_name = txt_file.name

    # Upload the file to vfolder
    with closing(run_user(["vfolder", "upload", vfolder_name, file_name])) as p:
        p.expect(EOF)
        assert "Done." in p.before.decode(), "File upload failed."

    # Check if the file has been successfully uploaded
    with closing(run_user(["vfolder", "ls", vfolder_name])) as p:
        p.expect(EOF)
        assert file_name in p.before.decode(), "File was not uploaded successfully."


@pytest.mark.dependency(depends=["test_create_vfolder", "test_upload_file"])
def test_rename_file(run_user: ClientRunnerFunc):
    """
    Test for renaming a file from the vfolder.
    !! Make sure you execute this test after 1. test_create_vfolder, 2. test_upload_file !!
    Otherwise, it will raise an error.
    """

    vfolder_name = "test_folder2"
    old_file_name = "test.txt"
    new_file_name = "new.txt"

    with closing(
        run_user(["vfolder", "rename-file", vfolder_name, old_file_name, new_file_name])
    ) as p:
        p.expect(EOF)
        assert "Renamed." in p.before.decode(), "File rename failed."

    with closing(run_user(["vfolder", "ls", vfolder_name])) as p:
        p.expect(EOF)
        assert new_file_name in p.before.decode(), "File was not renamed successfully."


@pytest.mark.dependency(depends=["test_create_vfolder", "test_upload_file", "test_rename_file"])
def test_download_file(run_user: ClientRunnerFunc):
    """
    Test for downloading a file from the vfolder.
    !! Make sure you execute this test after 1. test_create_vfolder, 2. test_upload_file, 3. test_rename_file !!
    Otherwise, it will raise an error.
    """

    vfolder_name = "test_folder2"
    file_name = "new.txt"

    # Download the file from vfolder
    with closing(run_user(["vfolder", "download", vfolder_name, file_name])) as p:
        p.expect(EOF)
        assert "Done." in p.before.decode(), "File download failed."

    # Check if the file has been successfully downloaded
    assert os.path.isfile(file_name), "File was not downloaded successfully."

    # remove the file for testing
    os.remove(file_name)


@pytest.mark.dependency(depends=["test_create_vfolder"])
def test_mkdir_vfolder(run_user: ClientRunnerFunc):
    """
    Test for creating an empty directory in the vfolder.
    !! Make sure you execute this test after test_create_vfolder !!
    Otherwise, it will raise an error.
    """

    vfolder_name = "test_folder2"
    dir_paths = ["tmp", "test/dir"]

    # Create directory in the vfolder
    with closing(run_user(["vfolder", "mkdir", vfolder_name, dir_paths[0]])) as p:
        p.expect(EOF)
        assert "Successfully created" in p.before.decode(), "Directory creation failed."

    # Create already existing directory with exist-ok option
    with closing(run_user(["vfolder", "mkdir", "-e", vfolder_name, dir_paths[0]])) as p:
        p.expect(EOF)
        assert (
            "Successfully created" in p.before.decode()
        ), "Exist-ok option does not work properly."

    # Test whether the parent directory is created automatically
    with closing(run_user(["vfolder", "mkdir", "-p", vfolder_name, dir_paths[1]])) as p:
        p.expect(EOF)
        assert (
            "Successfully created" in p.before.decode()
        ), "The parent directory is not created automatically."


@pytest.mark.dependency(
    depends=["test_create_vfolder", "test_upload_file", "test_rename_file", "test_mkdir_vfolder"]
)
def test_mv_file(run_user: ClientRunnerFunc):
    """
    Test for moving a file within the vfolder.
    !! Make sure you execute this test after 1. test_create_vfolder, 2. test_upload_file, 3. test_rename_file, 4. test_mkdir_vfolder !!
    Otherwise, it will raise an error.
    """

    vfolder_name = "test_folder2"
    dir_path = "tmp"
    file_name = "new.txt"

    with closing(
        run_user(["vfolder", "mv", vfolder_name, file_name, f"{dir_path}/{file_name}"])
    ) as p:
        p.expect(EOF)
        assert "Moved." in p.before.decode(), "File move failed."

    with closing(run_user(["vfolder", "ls", vfolder_name])) as p:
        p.expect(EOF)
        assert file_name not in p.before.decode(), "File was not moved successfully."

    with closing(run_user(["vfolder", "ls", vfolder_name, dir_path])) as p:
        p.expect(EOF)
        assert file_name in p.before.decode(), "File was not moved successfully."


@pytest.mark.dependency(depends=["test_create_vfolder", "test_rename_file"])
def test_delete_vfolder(run_user: ClientRunnerFunc):
    """
    Test delete vfolder function.
    !! Make sure you execute this test after 1. test_create_vfolder, 2. test_rename_vfolder !!
    Otherwise, it will raise an error.
    """
    print("[ Delete vfolder ]")
    with closing(run_user(["vfolder", "delete", "test_folder2"])) as p:
        p.expect(EOF)
        assert "Deleted" in p.before.decode(), "Test folder 2 not deleted successfully."

    with closing(run_user(["vfolder", "delete", "test_folder3"])) as p:
        p.expect(EOF)
        assert "Deleted" in p.before.decode(), "Test folder 3 not deleted successfully."


def test_delete_vfolder_the_same_vfolder_name(
    run_user: ClientRunnerFunc, run_user2: ClientRunnerFunc
):
    """
    Test delete vfolder function.
    Delete two vfolders that have the same name.
    """
    print("[ Delete vfolder same name ]")
    vfolder_name = "test_folder_name"
    with closing(run_user(["vfolder", "create", vfolder_name, "local:volume1"])) as p:
        p.expect(EOF)

    with closing(run_user2(["vfolder", "create", vfolder_name, "local:volume1"])) as p:
        p.expect(EOF)

    with closing(run_user(["vfolder", "delete", vfolder_name])) as p:
        p.expect(EOF)
        assert (
            "Deleted" in p.before.decode()
        ), "Test folder created by user not deleted successfully."

    with closing(run_user2(["vfolder", "delete", vfolder_name])) as p:
        p.expect(EOF)
        assert (
            "Deleted" in p.before.decode()
        ), "Test folder created by user2 not deleted successfully."


def test_list_vfolder(run_user: ClientRunnerFunc):
    """
    Test list vfolder function.
    """
    with closing(run_user(["--output=json", "vfolder", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        folder_list = loaded.get("items")
        assert isinstance(folder_list, list)


def get_folder_from_list(folders: list, foldername: str) -> dict:
    for folder in folders:
        if folder.get("name", "") == foldername:
            return folder
    return {}
