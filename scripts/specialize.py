import argparse
import shutil
from pathlib import Path


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copyfile(src, dst)


def populate_setup_cfg(pkg_name: str) -> None:
    pkg_root = Path('packages') / pkg_name
    root = Path('.')
    shutil.copyfile(pkg_root / 'setup.cfg', root / 'setup.cfg')


def populate_manifest(pkg_name: str) -> None:
    pkg_root = Path('packages') / pkg_name
    root = Path('.')
    _copy_if_exists(pkg_root / 'MANIFEST.in', root / 'MANIFEST.in')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pkg_name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    populate_setup_cfg(args.pkg_name)
    populate_manifest(args.pkg_name)


if __name__ == "__main__":
    main()
