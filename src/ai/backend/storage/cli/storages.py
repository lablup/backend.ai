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


def _make_encrypted_payload(
    bucket: str,
    key: str,
    secret: str,
    expiration: Optional[int] = None,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    payload = {
        "bucket": bucket,
        "key": key,
        "iat": int(time.time()),
        # TODO: Move constant to common
        "exp": int(time.time()) + (expiration or 300),
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
    storage_name: str,
    bucket_name: str,
    token: str,
) -> PresignedUploadData:
    """Get presigned upload URL from storage API."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.post(
            f"{storage_url}/v1/storages/s3/{storage_name}/buckets/{bucket_name}/file/presigned/upload",
            headers=headers,
        ) as response:
            if response.status != 200:
                # Parse API error responses for user-friendly messages
                if response.status == 400:
                    raise click.ClickException("Invalid request - check your parameters")
                elif response.status == 401:
                    raise click.ClickException("Authentication failed - check your secret key")
                elif response.status == 404:
                    raise click.ClickException("Storage or bucket not found")
                else:
                    raise click.ClickException(
                        f"Failed to get presigned upload URL (HTTP {response.status})"
                    )
            data = await response.json()
            return PresignedUploadData(**data)


async def get_presigned_download_url(
    storage_url: str,
    storage_name: str,
    bucket_name: str,
    token: str,
) -> dict:
    """Get presigned download URL from storage API."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(
            f"{storage_url}/v1/storages/s3/{storage_name}/buckets/{bucket_name}/file/presigned/download",
            headers=headers,
        ) as response:
            if response.status != 200:
                # Parse API error responses for user-friendly messages
                if response.status == 400:
                    raise click.ClickException("Invalid request - check your parameters")
                elif response.status == 401:
                    raise click.ClickException("Authentication failed - check your secret key")
                elif response.status == 404:
                    raise click.ClickException("Storage, bucket, or file not found")
                else:
                    raise click.ClickException(
                        f"Failed to get presigned download URL (HTTP {response.status})"
                    )
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

                    # Parse S3 XML error response for user-friendly messages
                    if "AccessDenied" in error_text:
                        raise click.ClickException("Access denied - check your credentials")
                    elif "SignatureDoesNotMatch" in error_text:
                        raise click.ClickException("Authentication failed - invalid signature")
                    elif "EntityTooLarge" in error_text:
                        raise click.ClickException("File too large for upload")
                    elif "RequestTimeTooSkewed" in error_text or "TokenExpired" in error_text:
                        raise click.ClickException("Request expired - try again")
                    else:
                        # For other errors, provide a generic message
                        raise click.ClickException(
                            f"Failed to upload file (HTTP {response.status})"
                        )


async def download_file_from_presigned_url(
    presigned_url: str,
    output_path: Path,
) -> None:
    """Download file using presigned URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(presigned_url) as response:
            if response.status != 200:
                error_text = await response.text()

                # Parse S3 XML error response for user-friendly messages
                if response.status == 404 or "NoSuchKey" in error_text:
                    raise click.ClickException("File not found in storage")
                elif "AccessDenied" in error_text:
                    raise click.ClickException("Access denied - check your credentials")
                elif "SignatureDoesNotMatch" in error_text:
                    raise click.ClickException("Authentication failed - invalid signature")
                elif "RequestTimeTooSkewed" in error_text or "TokenExpired" in error_text:
                    raise click.ClickException("Request expired - try again")
                else:
                    # For other errors, provide a generic message
                    raise click.ClickException(f"Failed to download file (HTTP {response.status})")

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
    "--storage-name",
    required=True,
    help="Storage configuration name",
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
    "--expiration",
    type=int,
    default=300,
    help="Token expiration time in seconds (default: 300)",
)
@click.pass_obj
def upload(
    cli_ctx: CLIContext,
    storage_url: str,
    secret: str,
    storage_name: str,
    bucket: str,
    key: str,
    file_path: Path,
    expiration: int,
) -> None:
    """
    Upload a file to object storage using presigned URL.

    Example: backend.ai storage storages upload --secret mysecret --storage-name backendai-storage --bucket backendai-storage --key myfile.txt --file /path/to/local/file.txt
    """

    async def _upload():
        click.echo(f"Uploading {file_path} to {bucket}/{key}...")

        payload = _make_encrypted_payload(
            bucket=bucket,
            key=key,
            secret=secret,
            expiration=expiration,
        )

        try:
            presigned_data = await get_presigned_upload_url(
                storage_url, storage_name, bucket, payload
            )

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
    "--storage-name",
    required=True,
    help="Storage configuration name",
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
    default=300,
    help="Token expiration time in seconds",
)
@click.pass_obj
def download(
    cli_ctx: CLIContext,
    storage_url: str,
    secret: str,
    storage_name: str,
    bucket: str,
    key: str,
    output: Optional[Path],
    filename: Optional[str],
    expiration: int,
) -> None:
    """
    Download a file from object storage using presigned URL.

    Example: backend.ai storage storages download --secret mysecret --storage-name backendai-storage --bucket backendai-storage --key myfile.txt --output /path/to/local/file.txt
    """

    async def _download():
        # Determine output path
        if output:
            output_path = output
        else:
            output_path = Path(filename or os.path.basename(key) or "downloaded_file")

        click.echo(f"Downloading {storage_name}/{bucket}/{key} to {output_path}...")

        payload = _make_encrypted_payload(
            bucket=bucket,
            key=key,
            secret=secret,
            expiration=expiration,
            filename=filename,
        )

        try:
            presigned_data = await get_presigned_download_url(
                storage_url, storage_name, bucket, payload
            )
            presigned_url = presigned_data["url"]

            await download_file_from_presigned_url(presigned_url, output_path)
            click.echo(f"✅ Successfully downloaded {storage_name}/{bucket}/{key} to {output_path}")

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
    "--storage-name",
    required=True,
    help="Storage configuration name",
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
    default=300,
    help="Token expiration time in seconds (default: 300)",
)
@click.pass_obj
def info(
    cli_ctx: CLIContext,
    storage_url: str,
    secret: str,
    storage_name: str,
    bucket: str,
    key: str,
    expiration: int,
) -> None:
    """
    Get information about an object in storage.

    Example: backend.ai storage storages info --secret mysecret --storage-name backendai-storage --bucket backendai-storage --key myfile.txt
    """

    async def _info():
        click.echo(f"Getting info for {bucket}/{key}...")

        payload = _make_encrypted_payload(
            bucket=bucket,
            key=key,
            secret=secret,
            expiration=expiration,
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{storage_url}/v1/storages/s3/{storage_name}/buckets/{bucket}/files",
                    params={"token": payload},
                ) as response:
                    if response.status != 200:
                        # Parse API error responses for user-friendly messages
                        if response.status == 400:
                            raise click.ClickException("Invalid request - check your parameters")
                        elif response.status == 401:
                            raise click.ClickException(
                                "Authentication failed - check your secret key"
                            )
                        elif response.status == 404:
                            raise click.ClickException("Storage, bucket, or file not found")
                        else:
                            raise click.ClickException(
                                f"Failed to get object info (HTTP {response.status})"
                            )

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
