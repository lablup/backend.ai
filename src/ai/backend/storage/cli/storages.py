import asyncio
import os
import time
from pathlib import Path
from typing import Optional

import aiohttp
import click
import jwt
from pydantic import BaseModel

from .context import CLIContext


class PresignedUploadData(BaseModel):
    """Pydantic model for presigned upload URL data from API."""

    url: str
    fields: dict[str, str]


@click.group()
def cli() -> None:
    """Storages management commands."""
    pass


def create_jwt_token(
    operation: str,
    bucket: str,
    key: str,
    secret: str,
    expiration: Optional[int] = None,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """Create JWT token for storage operations."""
    payload = {
        "op": operation,
        "bucket": bucket,
        "key": key,
        "iat": int(time.time()),
        "exp": int(time.time()) + (expiration or 3600),
    }

    if content_type:
        payload["content_type"] = content_type
    if filename:
        payload["filename"] = filename
    if expiration:
        payload["expiration"] = expiration

    return jwt.encode(payload, secret, algorithm="HS256")


async def get_presigned_upload_url(
    storage_url: str,
    token: str,
) -> PresignedUploadData:
    """Get presigned upload URL from storage API."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{storage_url}/storages/s3/presigned-upload-url", params={"token": token}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise click.ClickException(f"Failed to get presigned upload URL: {error_text}")
            data = await response.json()
            return PresignedUploadData(**data)


async def get_presigned_download_url(
    storage_url: str,
    token: str,
) -> dict:
    """Get presigned download URL from storage API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{storage_url}/storages/s3/presigned-download-url", params={"token": token}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise click.ClickException(f"Failed to get presigned download URL: {error_text}")
            return await response.json()


async def upload_file_to_presigned_url(
    presigned_data: PresignedUploadData,
    file_path: Path,
) -> None:
    """Upload file using presigned URL."""
    url = presigned_data.url
    fields = presigned_data.fields

    # Prepare form data
    data = aiohttp.FormData()
    for key, value in fields.items():
        data.add_field(key, value)

    # Add file
    with file_path.open("rb") as f:
        data.add_field("file", f, filename=file_path.name)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status not in (200, 204):
                    error_text = await response.text()
                    raise click.ClickException(f"Failed to upload file: {error_text}")


async def download_file_from_presigned_url(
    presigned_url: str,
    output_path: Path,
) -> None:
    """Download file using presigned URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(presigned_url) as response:
            if response.status != 200:
                error_text = await response.text()
                raise click.ClickException(f"Failed to download file: {error_text}")

            with output_path.open("wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)


@cli.command()
@click.option(
    "--storage-url",
    default="http://localhost:6021",
    help="Storage proxy server URL",
)
@click.option(
    "--secret",
    required=True,
    help="JWT secret for token generation",
)
@click.option(
    "--bucket",
    required=True,
    help="S3 bucket name",
)
@click.option(
    "--key",
    required=True,
    help="S3 object key (destination path in bucket)",
)
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Local file path to upload",
)
@click.option(
    "--content-type",
    help="Content type of the file (auto-detected if not provided)",
)
@click.option(
    "--expiration",
    type=int,
    default=3600,
    help="Token expiration time in seconds (default: 3600)",
)
@click.pass_obj
def upload(
    cli_ctx: CLIContext,
    storage_url: str,
    secret: str,
    bucket: str,
    key: str,
    file_path: Path,
    content_type: Optional[str],
    expiration: int,
) -> None:
    """
    Upload a file to object storage using presigned URL.

    Example: backend.ai storage storages upload --secret mysecret --bucket test-bucket --key myfile.txt --file /path/to/local/file.txt
    """

    async def _upload():
        click.echo(f"Uploading {file_path} to {bucket}/{key}...")

        # Auto-detect content type if not provided
        if not content_type:
            import mimetypes

            detected_type, _ = mimetypes.guess_type(str(file_path))
            content_type_to_use = detected_type or "application/octet-stream"
        else:
            content_type_to_use = content_type

        # Create JWT token for presigned upload
        token = create_jwt_token(
            operation="presigned_upload",
            bucket=bucket,
            key=key,
            secret=secret,
            expiration=expiration,
            content_type=content_type_to_use,
        )

        try:
            # Get presigned upload URL
            presigned_data = await get_presigned_upload_url(storage_url, token)

            # Upload file
            await upload_file_to_presigned_url(presigned_data, file_path)

            click.echo(f"✅ Successfully uploaded {file_path.name} to {bucket}/{key}")

        except Exception as e:
            click.echo(f"❌ Upload failed: {e}", err=True)
            raise click.Abort()

    asyncio.run(_upload())


@cli.command()
@click.option(
    "--storage-url",
    default="http://localhost:6021",
    help="Storage proxy server URL",
)
@click.option(
    "--secret",
    required=True,
    help="JWT secret for token generation",
)
@click.option(
    "--bucket",
    required=True,
    help="S3 bucket name",
)
@click.option(
    "--key",
    required=True,
    help="S3 object key (source path in bucket)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Local output file path (default: use key filename)",
)
@click.option(
    "--filename",
    help="Filename hint for download (optional)",
)
@click.option(
    "--expiration",
    type=int,
    default=3600,
    help="Token expiration time in seconds (default: 3600)",
)
@click.pass_obj
def download(
    cli_ctx: CLIContext,
    storage_url: str,
    secret: str,
    bucket: str,
    key: str,
    output: Optional[Path],
    filename: Optional[str],
    expiration: int,
) -> None:
    """
    Download a file from object storage using presigned URL.

    Example: backend.ai storage storages download --secret mysecret --bucket test-bucket --key myfile.txt --output /path/to/local/file.txt
    """

    async def _download():
        # Determine output path
        if output:
            output_path = output
        else:
            output_path = Path(filename or os.path.basename(key) or "downloaded_file")

        click.echo(f"Downloading {bucket}/{key} to {output_path}...")

        # Create JWT token for presigned download
        token = create_jwt_token(
            operation="presigned_download",
            bucket=bucket,
            key=key,
            secret=secret,
            expiration=expiration,
            filename=filename,
        )

        try:
            # Get presigned download URL
            presigned_data = await get_presigned_download_url(storage_url, token)
            presigned_url = presigned_data["url"]

            # Download file
            await download_file_from_presigned_url(presigned_url, output_path)

            click.echo(f"✅ Successfully downloaded {bucket}/{key} to {output_path}")

        except Exception as e:
            click.echo(f"❌ Download failed: {e}", err=True)
            raise click.Abort()

    asyncio.run(_download())


@cli.command()
@click.option(
    "--storage-url",
    default="http://localhost:6021",
    help="Storage proxy server URL",
)
@click.option(
    "--secret",
    required=True,
    help="JWT secret for token generation",
)
@click.option(
    "--bucket",
    required=True,
    help="S3 bucket name",
)
@click.option(
    "--key",
    required=True,
    help="S3 object key",
)
@click.option(
    "--expiration",
    type=int,
    default=3600,
    help="Token expiration time in seconds (default: 3600)",
)
@click.pass_obj
def info(
    cli_ctx: CLIContext,
    storage_url: str,
    secret: str,
    bucket: str,
    key: str,
    expiration: int,
) -> None:
    """
    Get information about an object in storage.

    Example: backend.ai storage storages info --secret mysecret --bucket test-bucket --key myfile.txt
    """

    async def _info():
        click.echo(f"Getting info for {bucket}/{key}...")

        # Create JWT token for info operation
        token = create_jwt_token(
            operation="info",
            bucket=bucket,
            key=key,
            secret=secret,
            expiration=expiration,
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{storage_url}/storages/s3", params={"token": token}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise click.ClickException(f"Failed to get object info: {error_text}")

                    info_data = await response.json()

                    click.echo("📋 Object Information:")
                    click.echo(f"  Content Length: {info_data.get('content_length', 'N/A')}")
                    click.echo(f"  Content Type: {info_data.get('content_type', 'N/A')}")
                    click.echo(f"  Last Modified: {info_data.get('last_modified', 'N/A')}")
                    click.echo(f"  ETag: {info_data.get('etag', 'N/A')}")

        except Exception as e:
            click.echo(f"❌ Getting info failed: {e}", err=True)
            raise click.Abort()

    asyncio.run(_info())
