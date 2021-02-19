import logging
from datetime import datetime
from typing import Optional

from .s3 import S3
from .sftp import Sftp

logger = logging.getLogger(__name__)


class TransferException(Exception):
    pass


class SftpS3Interface:
    def __init__(self, *, sftp: Sftp, s3: S3):
        self.sftp_conn = sftp
        self.s3_client = s3

    def transfer_sftp_to_s3(self, filename: str, sftp_directory: str, download_path: str, s3_bucket: str, s3_key: str) -> str:
        """Download file from SFTP server, then upload it to S3. Returns path to file after it's downloaded."""
        t1 = datetime.now()
        logger.info(f"Transfer SFTP to S3 start time: {t1}")

        download_file_path = f"{download_path}{filename}"

        try:
            self.sftp_conn.get(f"{sftp_directory}/{filename}", download_file_path)

            if self.s3_client.enabled:
                self.s3_client.upload_file(download_file_path, s3_bucket, s3_key)
        except Exception as e:
            logger.error(f"Error transferring file {filename}: {e}.")
            raise TransferException(e)

        t2 = datetime.now()
        logger.info(f"File transfer from SFTP to S3 complete. Took {t2 - t1} seconds.")

        return download_file_path

    def transfer_s3_to_sftp(self, s3_bucket: str, s3_key: str, file_name: str, sftp_directory: str,
                            download_path: Optional[str] = "/tmp") -> str:
        """Download file from S3, then put it on SFTP server. Returns original file name."""
        self.sftp_conn.chdir(sftp_directory)

        t1 = datetime.now()
        logger.info(f"Transfer S3 to SFTP start time: {t1}")

        file_path = f"{download_path}/{file_name}"

        self.s3_client.download_file(s3_bucket, s3_key, file_path)

        try:
            self.sftp_conn.put(file_path)
        except Exception as e:
            logger.error(f"Error transferring file {file_name}: {e}.")
            raise TransferException(e)

        t2 = datetime.now()
        logger.info(f"File transfer from S3 to SFTP complete. Took {t2 - t1} seconds.")

        return file_name
