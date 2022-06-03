import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_create_vfolder(run: ClientRunnerFunc):
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
    with closing(run(['vfolder', 'create',  '-p', 'rw', 'test_folder1', 'local:volume1'])) as p:
        p.expect(EOF)
        assert 'Virtual folder "test_folder1" is created' in p.before.decode(), 'Test folder1 not created successfully.'

    with closing(run(['vfolder', 'create', '-p', 'ro', 'test_folder2', 'local:volume1'])) as p:
        p.expect(EOF)
        assert 'Virtual folder "test_folder2" is created' in p.before.decode(), 'Test folder2 not created successfully.'

    # Check if vfolder is created
    with closing(run(['--output=json', 'vfolder', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        folder_list = loaded.get('items')
        assert isinstance(folder_list, list), 'Error in listing test folders!'

    test_folder1 = get_folder_from_list(folder_list, 'test_folder1')
    test_folder2 = get_folder_from_list(folder_list, 'test_folder2')

    assert bool(test_folder1), 'Test folder 1 doesn\'t exist!'
    assert test_folder1.get('permission') == 'rw', 'Test folder 1 permission mismatch.'

    assert bool(test_folder2), 'Test folder 2 doesn\'t exist!'
    assert test_folder2.get('permission') == 'ro', 'Test folder 2 permission mismatch.'


def test_rename_vfolder(run: ClientRunnerFunc):
    """
    Test rename vfolder function.
    !! Make sure you execute this test after test_create_vfolder !!
    Otherwise, it will raise an error.
    """
    print("[ Rename vfolder ]")
    # Rename vfolder
    with closing(run(['vfolder', 'rename', 'test_folder1', 'test_folder3'])) as p:
        p.expect(EOF)
        assert 'Renamed' in p.before.decode(), 'Test folder1 not renamed successfully.'

    # Check if vfolder is updated
    with closing(run(['--output=json', 'vfolder', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        folder_list = loaded.get('items')
        assert isinstance(folder_list, list), 'Error in listing test folders!'

    test_folder3 = get_folder_from_list(folder_list, 'test_folder3')
    assert bool(test_folder3), 'Test folder 3 doesn\'t exist!'


def test_delete_vfolder(run: ClientRunnerFunc):
    """
    Test delete vfolder function.
    !! Make sure you execute this test after 1. test_create_vfolder, 2. test_rename_vfolder !!
    Otherwise, it will raise an error.
    """
    print("[ Delete vfolder ]")
    with closing(run(['vfolder', 'delete', 'test_folder2'])) as p:
        p.expect(EOF)
        assert 'Deleted' in p.before.decode(), 'Test folder 2 not deleted successfully.'

    with closing(run(['vfolder', 'delete', 'test_folder3'])) as p:
        p.expect(EOF)
        assert 'Deleted' in p.before.decode(), 'Test folder 3 not deleted successfully.'


def test_list_vfolder(run: ClientRunnerFunc):
    """
    Test list vfolder function.
    """
    with closing(run(['--output=json', 'vfolder', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        folder_list = loaded.get('items')
        assert isinstance(folder_list, list)


def get_folder_from_list(folders: list, foldername: str) -> dict:
    for folder in folders:
        if folder.get('name', '') == foldername:
            return folder
    return {}
