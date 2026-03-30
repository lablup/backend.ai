import re
from pathlib import Path

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server


def get_major_version(version: str) -> str:
    """Return major.minor from a semantic version string.

    Accepts either "major.minor" (returned as-is) or a longer string like
    "major.minor.patch" where the leading major.minor is extracted.
    """
    if re.match(r"^\d+\.\d+$", version):
        return version
    match = re.match(r"^(\d+\.\d+)", version)
    if match:
        return match.group(1)
    raise ValueError(f"Invalid version format: {version}")


def ensure_file_exists(
    uri: str,
    local_dest: str | Path | None = None,
    sha256sum: str | None = None,
    force: bool = False,
) -> Path:
    """
    Ensure a file exists at the specified path, downloading it if necessary.

    Args:
        uri: Source URI (http:// or local file path)
        local_dest: Destination path
        sha256sum: Optional SHA256 checksum for validation
        force: If True, always overwrite existing files
    """
    if uri.startswith("http"):
        if not local_dest:
            local_dest = Path("/tmp") / Path(uri).name
        files.download(
            name=f"Download file from {uri} to {local_dest}",
            src=uri,
            dest=str(local_dest),
            sha256sum=sha256sum,
            force=force,
        )
        file_path = local_dest
    else:
        if not host.get_fact(File, uri):
            raise FileNotFoundError(f"File not found at {uri}")
        file_path = Path(uri)
        if local_dest:
            if force:
                server.shell(
                    name=f"Copy file from {file_path} to {local_dest} (force)",
                    commands=[f"cp -rp {file_path} {local_dest}"],
                )
            else:
                server.shell(
                    name=f"Copy file from {file_path} to {local_dest} if not exists",
                    commands=[f"test -e {local_dest} || cp -rp {file_path} {local_dest}"],
                )
            file_path = local_dest

    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path


def load_container_image(container_image: str, local_archive_path: str | None = None) -> None:
    """
    Load a container image either from local archive.

    Args:
        container_image: Docker image name (e.g., "postgres:16.9-alpine")
        local_archive_path: Path to local tar.gz archive file (e.g., "{LOCAL_REPO_URI}/docker/postgres.tar.gz")
    """
    if local_archive_path:
        # Check if image exists and load if missing - all in one shell command
        archive_file = ensure_file_exists(local_archive_path)
        server.shell(
            name=f"Load {container_image} from archive if not exists",
            commands=[
                f"if docker image inspect {container_image} >/dev/null 2>&1; then "
                f"echo 'Image {container_image} already exists, skipping load'; "
                f"else "
                f"LOAD_OUT=$(docker load -i {archive_file}) || "
                f"(echo 'ERROR: docker load failed for {archive_file}' && exit 1); "
                f'echo "$LOAD_OUT"; '
                # If the archive lacks repo tags, docker load produces "Loaded image ID: sha256:..."
                # instead of "Loaded image: name:tag". Detect this and tag the image explicitly.
                f"if echo \"$LOAD_OUT\" | grep -q 'Loaded image ID:'; then "
                f"IMAGE_ID=$(echo \"$LOAD_OUT\" | grep 'Loaded image ID:' | grep -o 'sha256:[a-f0-9]*' | head -1); "
                f'if [ -z "$IMAGE_ID" ]; then '
                f"echo 'ERROR: Could not extract image ID from docker load output'; exit 1; "
                f"fi; "
                f'docker tag "$IMAGE_ID" {container_image} || '
                f'(echo "ERROR: Failed to tag $IMAGE_ID as {container_image}" && exit 1); '
                f'echo "Tagged $IMAGE_ID as {container_image}"; '
                f"fi; "
                f"fi"
            ],
        )


def deep_merge(base: dict, updates: dict) -> dict:
    """
    Recursively merge two dictionaries.

    Nested dictionaries are merged recursively, while non-dict values from
    `updates` overwrite those in `base`.

    Args:
        base: Base dictionary to merge into
        updates: Dictionary with updates to apply

    Returns:
        Merged dictionary (modifies and returns `base`)

    Example:
        >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> updates = {"b": {"d": 4, "e": 5}, "f": 6}
        >>> deep_merge(base, updates)
        {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
    """
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base
