import tempfile
from pathlib import Path

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext
from ai.backend.test.templates.template import TestCode

_CONTENT = "This is a test file for VFolder download."


class VFolderDownloadSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()

        uploaded_files: list[str] = []
        with tempfile.TemporaryDirectory() as upload_dir:
            upload_root = Path(upload_dir)
            uploaded_dir_name = upload_root.name

            for i in range(3):
                rel_path = f"{uploaded_dir_name}/temp_{i}.txt"
                uploaded_files.append(rel_path)
                (upload_root / f"temp_{i}.txt").write_text(_CONTENT)

            (upload_root / "nested").mkdir()
            (upload_root / "nested" / "inner.txt").write_text(_CONTENT)
            uploaded_files.append(f"{uploaded_dir_name}/nested/inner.txt")

            await client_session.VFolder(vfolder_meta.name).upload(
                [upload_root], basedir=upload_root.parent, recursive=True
            )

        with tempfile.TemporaryDirectory() as download_dir:
            download_root = Path(download_dir)
            (download_root / uploaded_dir_name / "nested").mkdir(parents=True, exist_ok=True)

            await client_session.VFolder(vfolder_meta.name).download(
                uploaded_files,
                basedir=download_root,
                max_retries=3,
            )

            for rel_path in uploaded_files:
                local_path = download_root / rel_path
                assert local_path.exists(), f"{local_path} is missing"
                assert local_path.read_text() == _CONTENT, f"{local_path} file content mismatch"
