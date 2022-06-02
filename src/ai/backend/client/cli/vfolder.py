from datetime import datetime
import json
from pathlib import Path
import sys

import click
import humanize
from tabulate import tabulate
from tqdm import tqdm

from ai.backend.cli.interaction import ask_yn
from ai.backend.client.config import DEFAULT_CHUNK_SIZE, APIConfig
from ai.backend.client.session import Session

from ..compat import asyncio_run
from ..session import AsyncSession
from .main import main
from .pretty import print_done, print_error, print_fail, print_info, print_wait, print_warn
from .params import ByteSizeParamType, ByteSizeParamCheckType, CommaSeparatedKVListParamType


@main.group()
def vfolder():
    """Set of vfolder operations"""


@vfolder.command()
def list_hosts():
    '''List the hosts of virtual folders that is accessible to the current user.'''
    with Session() as session:
        try:
            resp = session.VFolder.list_hosts()
            print("Default vfolder host: {}".format(resp['default']))
            print("Usable hosts: {}".format(', '.join(resp['allowed'])))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
def list_allowed_types():
    '''List allowed vfolder types.'''
    with Session() as session:
        try:
            resp = session.VFolder.list_allowed_types()
            print(resp)
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('host', type=str, default=None)
@click.option('-g', '--group', metavar='GROUP', type=str, default=None,
              help='Group ID or NAME. Specify this option if you want to create a group folder.')
@click.option('--unmanaged', 'host_path', type=bool, is_flag=True,
              help='Treats HOST as a mount point of unmanaged virtual folder. '
                   'This option can only be used by Admin or Superadmin.')
@click.option('-m', '--usage-mode', metavar='USAGE_MODE', type=str, default='general',
              help='Purpose of the folder. Normal folders are usually set to "general". '
                   'Available options: "general", "data" (provides data to users), '
                   'and "model" (provides pre-trained models).')
@click.option('-p', '--permission', metavar='PERMISSION', type=str, default='rw',
              help='Folder\'s innate permission. '
                   'Group folders can be shared as read-only by setting this option to "ro".'
                   'Invited folders override this setting by its own invitation permission.')
@click.option('-q', '--quota', metavar='QUOTA', type=ByteSizeParamCheckType(), default='0',
              help='Quota of the virtual folder. '
                   '(Use \'m\' for megabytes, \'g\' for gigabytes, and etc.) '
                   'Default is maximum amount possible.')
@click.option('--cloneable', '--allow-clone', type=bool, is_flag=True,
              help='Allows the virtual folder to be cloned by users.')
def create(name, host, group, host_path, usage_mode, permission, quota, cloneable):
    '''Create a new virtual folder.

    \b
    NAME: Name of a virtual folder.
    HOST: Name of a virtual folder host in which the virtual folder will be created.
    '''
    with Session() as session:
        try:
            if host_path:
                result = session.VFolder.create(
                    name=name,
                    unmanaged_path=host,
                    group=group,
                    usage_mode=usage_mode,
                    permission=permission,
                    quota=quota,
                    cloneable=cloneable,
                )
            else:
                result = session.VFolder.create(
                    name=name,
                    host=host,
                    group=group,
                    usage_mode=usage_mode,
                    permission=permission,
                    quota=quota,
                    cloneable=cloneable,
                )
            print('Virtual folder "{0}" is created.'.format(result['name']))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
def delete(name):
    '''Delete the given virtual folder. This operation is irreversible!

    NAME: Name of a virtual folder.
    '''
    with Session() as session:
        try:
            session.VFolder(name).delete()
            print_done('Deleted.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('old_name', type=str)
@click.argument('new_name', type=str)
def rename(old_name, new_name):
    '''Rename the given virtual folder. This operation is irreversible!
    You cannot change the vfolders that are shared by other users,
    and the new name must be unique among all your accessible vfolders
    including the shared ones.

    OLD_NAME: The current name of a virtual folder.
    NEW_NAME: The new name of a virtual folder.
    '''
    with Session() as session:
        try:
            session.VFolder(old_name).rename(new_name)
            print_done('Renamed.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
def info(name):
    '''Show the information of the given virtual folder.

    NAME: Name of a virtual folder.
    '''
    with Session() as session:
        try:
            result = session.VFolder(name).info()
            print('Virtual folder "{0}" (ID: {1})'
                  .format(result['name'], result['id']))
            print('- Owner:', result['is_owner'])
            print('- Permission:', result['permission'])
            print('- Number of files: {0}'.format(result['numFiles']))
            print('- Ownership Type: {0}'.format(result['type']))
            print('- Permission:', result['permission'])
            print('- Usage Mode: {0}'.format(result.get('usage_mode', '')))
            print('- Group ID: {0}'.format(result['group']))
            print('- User ID: {0}'.format(result['user']))
            print('- Clone Allowed: {0}'.format(result['cloneable']))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command(context_settings={'show_default': True})  # bug: pallets/click#1565 (fixed in 8.0)
@click.argument('name', type=str)
@click.argument('filenames', type=Path, nargs=-1)
@click.option('-b', '--base-dir', type=Path, default=None,
              help='Set the parent directory from where the file is uploaded.  '
                   '[default: current working directry]')
@click.option('--chunk-size', type=ByteSizeParamType(),
              default=humanize.naturalsize(DEFAULT_CHUNK_SIZE, binary=True, gnu=True),
              help='Transfer the file with the given chunk size with binary suffixes (e.g., "16m"). '
                   'Set this between 8 to 64 megabytes for high-speed disks (e.g., SSD RAID) '
                   'and networks (e.g., 40 GbE) for the maximum throughput.')
@click.option('--override-storage-proxy',
              type=CommaSeparatedKVListParamType(), default=None,
              help='Overrides storage proxy address. '
                   'The value must shape like "X1=Y1,X2=Y2...". '
                   'Each Yn address must at least include the IP address '
                   'or the hostname and may include the protocol part and the port number to replace.')
def upload(name, filenames, base_dir, chunk_size, override_storage_proxy):
    '''
    TUS Upload a file to the virtual folder from the current working directory.
    The files with the same names will be overwirtten.

    \b
    NAME: Name of a virtual folder.
    FILENAMES: Paths of the files to be uploaded.
    '''
    with Session() as session:
        try:
            session.VFolder(name).upload(
                filenames,
                basedir=base_dir,
                chunk_size=chunk_size,
                show_progress=True,
                address_map=override_storage_proxy or APIConfig.DEFAULTS['storage_proxy_address_map'],
            )
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command(context_settings={'show_default': True})  # bug: pallets/click#1565 (fixed in 8.0)
@click.argument('name', type=str)
@click.argument('filenames', type=Path, nargs=-1)
@click.option('-b', '--base-dir', type=Path, default=None,
              help='Set the parent directory from where the file is uploaded.  '
                   '[default: current working directry]')
@click.option('--chunk-size', type=ByteSizeParamType(),
              default=humanize.naturalsize(DEFAULT_CHUNK_SIZE, binary=True, gnu=True),
              help='Transfer the file with the given chunk size with binary suffixes (e.g., "16m"). '
                   'Set this between 8 to 64 megabytes for high-speed disks (e.g., SSD RAID) '
                   'and networks (e.g., 40 GbE) for the maximum throughput.')
@click.option('--override-storage-proxy',
              type=CommaSeparatedKVListParamType(), default=None,
              help='Overrides storage proxy address. '
                   'The value must shape like "X1=Y1,X2=Y2...". '
                   'Each Yn address must at least include the IP address '
                   'or the hostname and may include the protocol part and the port number to replace.')
def download(name, filenames, base_dir, chunk_size, override_storage_proxy):
    '''
    Download a file from the virtual folder to the current working directory.
    The files with the same names will be overwirtten.

    \b
    NAME: Name of a virtual folder.
    FILENAMES: Paths of the files to be downloaded inside a vfolder.
    '''
    with Session() as session:
        try:
            session.VFolder(name).download(
                filenames,
                basedir=base_dir,
                chunk_size=chunk_size,
                show_progress=True,
                address_map=override_storage_proxy or APIConfig.DEFAULTS['storage_proxy_address_map'],
            )
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('filename', type=Path)
def request_download(name, filename):
    '''
    Request JWT-formated download token for later use.

    \b
    NAME: Name of a virtual folder.
    FILENAME: Path of the file to be downloaded.
    '''
    with Session() as session:
        try:
            response = json.loads(session.VFolder(name).request_download(filename))
            print_done(f'Download token: {response["token"]}')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('filenames', nargs=-1)
def cp(filenames):
    '''An scp-like shortcut for download/upload commands.

    FILENAMES: Paths of the files to operate on. The last one is the target while all
               others are the sources.  Either source paths or the target path should
               be prefixed with "<vfolder-name>:" like when using the Linux scp
               command to indicate if it is a remote path.
    '''
    raise NotImplementedError


@vfolder.command()
@click.argument('name', type=str)
@click.argument('path', type=str)
@click.option('-p', '--parents', default=False, is_flag=True,
              help='Make missing parents of this path as needed')
@click.option('-e', '--exist-ok', default=False, is_flag=True,
              help='Skip an error caused by file not found')
def mkdir(name, path, parents, exist_ok):
    '''Create an empty directory in the virtual folder.

    \b
    NAME: Name of a virtual folder.
    PATH: The name or path of directory. Parent directories are created automatically
          if they do not exist.
    '''
    with Session() as session:
        try:
            session.VFolder(name).mkdir(path, parents=parents, exist_ok=exist_ok)
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('target_path', type=str)
@click.argument('new_name', type=str)
def rename_file(name, target_path, new_name):
    '''
    Rename a file or a directory in a virtual folder.

    \b
    NAME: Name of a virtual folder.
    TARGET_PATH: The target path inside a virtual folder (file or directory).
    NEW_NAME: New name of the target (should not contain slash).
    '''
    with Session() as session:
        try:
            session.VFolder(name).rename_file(target_path, new_name)
            print_done('Renamed.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('src', type=str)
@click.argument('dst', type=str)
def mv(name, src, dst):
    '''
    Move a file or a directory within a virtual folder.
    If the destination is a file and already exists, it will be overwritten.
    If the destination is a directory, the source file or directory
    is moved inside it.

    \b
    NAME: Name of a virtual folder.
    SRC: The relative path of the source file or directory inside a virtual folder
    DST: The relative path of the destination file or directory inside a virtual folder.
    '''
    with Session() as session:
        try:
            session.VFolder(name).move_file(src, dst)
            print_done('Moved.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command(aliases=['delete-file'])
@click.argument('name', type=str)
@click.argument('filenames', nargs=-1)
@click.option('-r', '--recursive', is_flag=True,
              help='Enable recursive deletion of directories.')
def rm(name, filenames, recursive):
    '''
    Delete files in a virtual folder.
    If one of the given paths is a directory and the recursive option is enabled,
    all its content and the directory itself are recursively deleted.

    This operation is irreversible!

    \b
    NAME: Name of a virtual folder.
    FILENAMES: Paths of the files to delete.
    '''
    with Session() as session:
        try:
            if not ask_yn():
                print_info('Cancelled')
                sys.exit(1)
            session.VFolder(name).delete_files(
                filenames,
                recursive=recursive)
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('path', metavar='PATH', nargs=1, default='.')
def ls(name, path):
    """
    List files in a path of a virtual folder.

    \b
    NAME: Name of a virtual folder.
    PATH: Path inside vfolder.
    """
    with Session() as session:
        try:
            print_wait('Retrieving list of files in "{}"...'.format(path))
            result = session.VFolder(name).list_files(path)
            if 'error_msg' in result and result['error_msg']:
                print_fail(result['error_msg'])
                return
            files = json.loads(result['files'])
            table = []
            headers = ['file name', 'size', 'modified', 'mode']
            for file in files:
                mdt = datetime.fromtimestamp(file['mtime'])
                mtime = mdt.strftime('%b %d %Y %H:%M:%S')
                row = [file['filename'], file['size'], mtime, file['mode']]
                table.append(row)
            print_done('Retrived.')
            print(tabulate(table, headers=headers))
        except Exception as e:
            print_error(e)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('emails', type=str, nargs=-1, required=True)
@click.option('-p', '--perm', metavar='PERMISSION', type=str, default='rw',
              help='Permission to give. "ro" (read-only) / "rw" (read-write) / "wd" (write-delete).')
def invite(name, emails, perm):
    """Invite other users to access a user-type virtual folder.

    \b
    NAME: Name of a virtual folder.
    EMAILS: Emails to invite.
    """
    with Session() as session:
        try:
            assert perm in ['rw', 'ro', 'wd'], 'Invalid permission: {}'.format(perm)
            result = session.VFolder(name).invite(perm, emails)
            invited_ids = result.get('invited_ids', [])
            if len(invited_ids) > 0:
                print('Invitation sent to:')
                for invitee in invited_ids:
                    print('\t- ' + invitee)
            else:
                print('No users found. Invitation was not sent.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
def invitations():
    """List and manage received invitations.
    """
    with Session() as session:
        try:
            result = session.VFolder.invitations()
            invitations = result.get('invitations', [])
            if len(invitations) < 1:
                print('No invitations.')
                return
            print('List of invitations (inviter, vfolder id, permission):')
            for cnt, inv in enumerate(invitations):
                if inv['perm'] == 'rw':
                    perm = 'read-write'
                elif inv['perm'] == 'ro':
                    perm = 'read-only'
                else:
                    perm = inv['perm']
                print('[{}] {}, {}, {}'.format(cnt + 1, inv['inviter'],
                                               inv['vfolder_id'], perm))

            selection = input('Choose invitation number to manage: ')
            if selection.isdigit():
                selection = int(selection) - 1
            else:
                return
            if 0 <= selection < len(invitations):
                while True:
                    action = input('Choose action. (a)ccept, (r)eject, (c)ancel: ')
                    if action.lower() == 'a':
                        session.VFolder.accept_invitation(invitations[selection]['id'])
                        msg = (
                            'You can now access vfolder {} ({})'.format(
                                invitations[selection]['vfolder_name'],
                                invitations[selection]['id'],
                            )
                        )
                        print(msg)
                        break
                    elif action.lower() == 'r':
                        session.VFolder.delete_invitation(invitations[selection]['id'])
                        msg = (
                            'vfolder invitation rejected: {} ({})'.format(
                                invitations[selection]['vfolder_name'],
                                invitations[selection]['id'],
                            )
                        )
                        print(msg)
                        break
                    elif action.lower() == 'c':
                        break
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('emails', type=str, nargs=-1, required=True)
@click.option('-p', '--perm', metavar='PERMISSION', type=str, default='rw',
              help='Permission to give. "ro" (read-only) / "rw" (read-write) / "wd" (write-delete).')
def share(name, emails, perm):
    """Share a group folder to users with overriding permission.

    \b
    NAME: Name of a (group-type) virtual folder.
    EMAILS: Emails to share.
    """
    with Session() as session:
        try:
            assert perm in ['rw', 'ro', 'wd'], 'Invalid permission: {}'.format(perm)
            result = session.VFolder(name).share(perm, emails)
            shared_emails = result.get('shared_emails', [])
            if len(shared_emails) > 0:
                print('Shared with {} permission to:'.format(perm))
                for _email in shared_emails:
                    print('\t- ' + _email)
            else:
                print('No users found. Folder is not shared.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('emails', type=str, nargs=-1, required=True)
def unshare(name, emails):
    """Unshare a group folder from users.

    \b
    NAME: Name of a (group-type) virtual folder.
    EMAILS: Emails to share.
    """
    with Session() as session:
        try:
            result = session.VFolder(name).unshare(emails)
            unshared_emails = result.get('unshared_emails', [])
            if len(unshared_emails) > 0:
                print('Unshared from:')
                for _email in unshared_emails:
                    print('\t- ' + _email)
            else:
                print('No users found. Folder is not unshared.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
def leave(name):
    '''Leave the shared virutal folder.

    NAME: Name of a virtual folder
    '''
    with Session() as session:
        try:
            vfolder_info = session.VFolder(name).info()
            if vfolder_info['type'] == 'group':
                print('You cannot leave a group virtual folder.')
                return
            if vfolder_info['is_owner']:
                print('You cannot leave a virtual folder you own. Consider using delete instead.')
                return
            session.VFolder(name).leave()
            print('Left the shared virtual folder "{}".'.format(name))

        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('target_name', type=str)
@click.argument('target_host', type=str)
@click.option('-m', '--usage-mode', metavar='USAGE_MODE', type=str, default='general',
              help='Purpose of the cloned virtual folder. '
                   'Default value is \'general\'.')
@click.option('-p', '--permission', metavar='PERMISSION', type=str, default='rw',
              help='Cloned virtual folder\'s permission. '
                   'Default value is \'rw\'.')
def clone(name, target_name, target_host, usage_mode, permission):
    """Clone a virtual folder.

    \b
    NAME: Name of the virtual folder to clone from.
    TARGET_NAME: Name of the virtual folder to clone to.
    TARGET_HOST: Name of a virtual folder host to which the virtual folder will be cloned.
    """
    with Session() as session:
        try:
            vfolder_info = session.VFolder(name).info()
            if not vfolder_info['cloneable']:
                print("Clone is not allowed for this virtual folder. "
                      "Please update the 'cloneable' option.")
                return
            result = session.VFolder(name).clone(
                target_name,
                target_host=target_host,
                usage_mode=usage_mode,
                permission=permission,
            )
            bgtask_id = result.get('bgtask_id')
        except Exception as e:
            print_error(e)
            sys.exit(1)

    async def clone_vfolder_tracker(bgtask_id):
        print_wait(
            "Cloning the vfolder... "
            "(This may take a while depending on its size and number of files!)",
        )
        async with AsyncSession() as session:
            try:
                bgtask = session.BackgroundTask(bgtask_id)
                completion_msg_func = lambda: print_done("Cloning the vfolder is complete.")
                async with bgtask.listen_events() as response:
                    # TODO: get the unit of progress from response
                    with tqdm(unit='bytes', disable=True) as pbar:
                        async for ev in response:
                            data = json.loads(ev.data)
                            if ev.event == 'bgtask_updated':
                                pbar.total = data['total_progress']
                                pbar.write(data['message'])
                                pbar.update(data['current_progress'] - pbar.n)
                            elif ev.event == 'bgtask_failed':
                                error_msg = data['message']
                                completion_msg_func = \
                                    lambda: print_fail(
                                        f"Error during the operation: {error_msg}",
                                    )
                            elif ev.event == 'bgtask_cancelled':
                                completion_msg_func = \
                                    lambda: print_warn(
                                        "The operation has been cancelled in the middle. "
                                        "(This may be due to server shutdown.)",
                                    )
            finally:
                completion_msg_func()

    if bgtask_id is None:
        print_done("Cloning the vfolder is complete.")
    else:
        asyncio_run(clone_vfolder_tracker(bgtask_id))


@vfolder.command()
@click.argument('name', type=str)
@click.option('-p', '--permission', type=str, metavar='PERMISSION',
              help="Folder's innate permission.")
@click.option('--set-cloneable', type=bool, metavar='BOOLEXPR',
              help="A boolean-interpretable string whether a virtual folder can be cloned. "
                   "If not set, the cloneable property is not changed.")
def update_options(name, permission, set_cloneable):
    """Update an existing virtual folder.

    \b
    NAME: Name of the virtual folder to update.
    """
    with Session() as session:
        try:
            vfolder_info = session.VFolder(name).info()
            if not vfolder_info['is_owner']:
                print("You cannot update virtual folder that you do not own.")
                return
            session.VFolder(name).update_options(
                name,
                permission=permission,
                cloneable=set_cloneable,
            )
            print_done("Updated.")
        except Exception as e:
            print_error(e)
            sys.exit(1)
