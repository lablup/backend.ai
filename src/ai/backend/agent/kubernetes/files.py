import logging
import os
from pathlib import Path
from typing import Dict

from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

# the names of following AWS variables follow boto3 convention.
s3_access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'dummy-access-key')
s3_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'dummy-secret-key')
s3_region = os.environ.get('AWS_REGION', 'ap-northeast-1')
s3_bucket = os.environ.get('AWS_S3_BUCKET', 'codeonweb')
s3_bucket_path = os.environ.get('AWS_S3_BUCKET_PATH', 'bucket')

if s3_access_key == 'dummy-access-key':
    log.info('Automatic ~/.output file S3 uploads is disabled.')


def relpath(path, base):
    return Path(path).resolve().relative_to(Path(base).resolve())


def scandir(root: Path, allowed_max_size: int):
    '''
    Scans a directory recursively and returns a dictionary of all files and
    their last modified time.
    '''
    file_stats: Dict[Path, float] = dict()
    if not isinstance(root, Path):
        root = Path(root)
    if not root.exists():
        return file_stats
    for entry in os.scandir(root):
        # Skip hidden files.
        if entry.name.startswith('.'):
            continue
        if entry.is_file():
            try:
                stat = entry.stat()
            except PermissionError:
                continue
            # Skip too large files!
            if stat.st_size > allowed_max_size:
                continue
            file_stats[Path(entry.path)] = stat.st_mtime
        elif entry.is_dir():
            try:
                file_stats.update(scandir(Path(entry.path), allowed_max_size))
            except PermissionError:
                pass
    return file_stats


def diff_file_stats(fs1, fs2):
    k2 = set(fs2.keys())
    k1 = set(fs1.keys())
    new_files = k2 - k1
    modified_files = set()
    for k in (k2 - new_files):
        if fs1[k] < fs2[k]:
            modified_files.add(k)
    return new_files | modified_files
