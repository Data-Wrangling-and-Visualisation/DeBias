import logging

import aiobotocore.session
from core.configs import S3Config

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self, config: S3Config):
        self.cfg = config

    async def upload(self, path: str, content: str) -> None:
        """
        Upload content to S3 at the specified path.

        Args:
            path: The path where the content will be uploaded in S3
            content: The string content to upload
        """
        session = aiobotocore.session.get_session()
        client_kwargs = {
            "region_name": self.cfg.region,
            "endpoint_url": self.cfg.endpoint,
            "aws_access_key_id": self.cfg.access_key,
            "aws_secret_access_key": self.cfg.secret_key,
        }
        async with session.create_client("s3", **client_kwargs) as client:
            logger.debug(f"uploading {path} to s3://{self.cfg.bucket_name}/{path}")
            await client.put_object(Bucket=self.cfg.bucket_name, Key=path, Body=content.encode("utf-8"))  # type: ignore

    async def download(self, path: str) -> str:
        """
        Download content from S3 at the specified path.

        Args:
            path: The path to download from S3

        Returns:
            The content as a string
        """
        session = aiobotocore.session.get_session()
        client_kwargs = {
            "region_name": self.cfg.region,
            "endpoint_url": self.cfg.endpoint,
            "aws_access_key_id": self.cfg.access_key,
            "aws_secret_access_key": self.cfg.secret_key,
        }

        async with session.create_client("s3", **client_kwargs) as client:
            logger.debug(f"downloading {path} from s3://{self.cfg.bucket_name}/{path}")
            response = await client.get_object(Bucket=self.cfg.bucket_name, Key=path)  # type: ignore
            async with response["Body"] as stream:
                data = await stream.read()
                return data.decode("utf-8")
