from unittest.mock import AsyncMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from ai.backend.storage.client.s3 import S3Client, S3ObjectInfo, S3PresignedUploadData


@pytest.fixture
def s3_client():
    """Create S3Client instance for testing"""
    return S3Client(
        bucket_name="test-bucket",
        endpoint_url="http://localhost:9000",
        region_name="us-east-1",
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key",
    )


@pytest.mark.asyncio
async def test_upload_stream_success(s3_client: S3Client):
    """Test successful stream upload"""

    async def data_stream():
        yield b"chunk1"
        yield b"chunk2"
        yield b"chunk3"

    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.upload_stream(
            data_stream(), "test/key.txt", content_type="text/plain"
        )

        assert result is True
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args[1]
        assert call_args["Bucket"] == "test-bucket"
        assert call_args["Key"] == "test/key.txt"
        assert call_args["Body"] == b"chunk1chunk2chunk3"
        assert call_args["ContentType"] == "text/plain"


@pytest.mark.asyncio
async def test_upload_stream_no_credentials(s3_client: S3Client):
    """Test upload stream with no credentials error"""

    async def data_stream():
        yield b"test data"

    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.put_object.side_effect = NoCredentialsError()
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.upload_stream(data_stream(), "test/key.txt")

        assert result is False


@pytest.mark.asyncio
async def test_upload_stream_client_error(s3_client: S3Client):
    """Test upload stream with client error"""

    async def data_stream():
        yield b"test data"

    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "PutObject"
        )
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.upload_stream(data_stream(), "test/key.txt")

        assert result is False


@pytest.mark.asyncio
async def test_download_stream_success(s3_client: S3Client):
    """Test successful stream download"""
    test_data = b"This is test file content"

    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(side_effect=[test_data[:10], test_data[10:], b""])
        mock_client.get_object.return_value = {"Body": mock_body}
        mock_session.return_value.__aenter__.return_value = mock_client

        chunks = []
        async for chunk in s3_client.download_stream("test/key.txt"):
            chunks.append(chunk)

        assert b"".join(chunks) == test_data
        mock_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="test/key.txt")


@pytest.mark.asyncio
async def test_download_stream_not_found(s3_client: S3Client):
    """Test download stream with object not found"""
    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "GetObject",
        )
        mock_session.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ClientError):
            async for chunk in s3_client.download_stream("nonexistent/key.txt"):
                pass


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_success(s3_client: S3Client):
    """Test successful presigned upload URL generation"""
    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.generate_presigned_post.return_value = {
            "url": "https://test-bucket.s3.amazonaws.com/",
            "fields": {
                "key": "test/key.txt",
                "policy": "eyJleHBpcmF0aW9uIjoi...",
                "x-amz-algorithm": "AWS4-HMAC-SHA256",
            },
        }
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.generate_presigned_upload_url(
            "test/key.txt",
            expiration=3600,
            content_type="text/plain",
            content_length_range=(100, 1000),
        )

        assert result is not None
        assert isinstance(result, S3PresignedUploadData)
        assert result.url == "https://test-bucket.s3.amazonaws.com/"
        assert result.key == "test/key.txt"
        assert result.fields is not None


@pytest.mark.asyncio
async def test_generate_presigned_download_url_success(s3_client: S3Client):
    """Test successful presigned download URL generation"""
    expected_url = "https://test-bucket.s3.amazonaws.com/test/key.txt?..."

    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.generate_presigned_url.return_value = expected_url
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.generate_presigned_download_url("test/key.txt", expiration=3600)

        assert result == expected_url
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/key.txt"},
            ExpiresIn=3600,
        )


@pytest.mark.asyncio
async def test_get_object_info_success(s3_client: S3Client):
    """Test successful object info retrieval"""
    from datetime import datetime

    expected_info = {
        "ContentLength": 1024,
        "ContentType": "text/plain",
        "LastModified": datetime.now(),
        "ETag": '"abcd1234efgh5678"',
        "Metadata": {"user": "test"},
    }

    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.head_object.return_value = expected_info
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.get_object_info("test/key.txt")

        assert result is not None
        assert isinstance(result, S3ObjectInfo)
        assert result.content_length == 1024
        assert result.content_type == "text/plain"
        assert result.etag == '"abcd1234efgh5678"'
        assert result.metadata == {"user": "test"}


@pytest.mark.asyncio
async def test_get_object_info_not_found(s3_client: S3Client):
    """Test object info retrieval with object not found"""
    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "HeadObject",
        )
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.get_object_info("nonexistent/key.txt")

        assert result is None


@pytest.mark.asyncio
async def test_delete_object_success(s3_client: S3Client):
    """Test successful object deletion"""
    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.delete_object("test/key.txt")
        assert result is True
        mock_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="test/key.txt")


@pytest.mark.asyncio
async def test_delete_object_error(s3_client: S3Client):
    """Test object deletion with error"""
    with patch.object(s3_client.session, "client") as mock_session:
        mock_client = AsyncMock()
        mock_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "DeleteObject"
        )
        mock_session.return_value.__aenter__.return_value = mock_client

        result = await s3_client.delete_object("test/key.txt")
        assert result is False
