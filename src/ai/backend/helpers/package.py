from collections import namedtuple
from pathlib import Path
import pkg_resources
import site
import subprocess
import sys

Package = namedtuple('Package', 'name version is_user')

__all__ = (
    'install',
)


def install(pkgname, force_install=False):
    '''
    Install a Python package from pypi.org or the given index server.
    The package is installed inside the user site directory.
    '''

    if not force_install:
        user_path = Path(site.USER_SITE).resolve()
        installed_pkgs = []
        for pkg in pkg_resources.working_set:
            pkg_path = Path(pkg.location).resolve()
            is_user = user_path in pkg_path.parents
            installed_pkgs.append(Package(pkg.key, pkg.version, is_user))

        for pkg in installed_pkgs:
            if pkgname.lower() == pkg.name.lower():
                print(f"'{pkg.name}' is already installed (version: {pkg.version}).")
                return

    sys.stdout.flush()
    cmdargs = [sys.executable, '-m', 'pip', 'install', '--user']
    if force_install:
        cmdargs.append('-I')
    cmdargs.append(pkgname)
    subprocess.call(cmdargs)
    sys.stdout.flush()

    # Ensure the user site directory to be in sys.path
    if site.USER_SITE not in sys.path:
        sys.path.insert(0, site.USER_SITE)
