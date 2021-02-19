import logging
import os
from base64 import decodebytes
from io import StringIO
from typing import Optional

import pysftp

logger = logging.getLogger(__name__)


class Sftp(pysftp.Connection):
    """Wrapper of pysftp.Connection. Handles proper parsing of private keys and host fingerprints."""

    def __init__(self, *, host: str, port: int = 22, username: str, password: Optional[str] = None,
                 private_key: Optional[str] = None, passphrase: Optional[str] = None,
                 host_fingerprint: Optional[str] = None, **kwargs):
        cnopts = None

        if private_key:
            private_key = pysftp.RSAKey.from_private_key(StringIO(private_key), passphrase)

        # Add host key when not on local, where it can be stored in /.ssh/known_hosts.
        if os.getenv("PROJECT_ENV", "local") != "local":
            fingerprint = host_fingerprint.encode()
            host_key = pysftp.RSAKey(data=decodebytes(fingerprint))
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys.add(host, 'ssh-rsa', host_key)

        super(Sftp, self).__init__(host=host,
                                   username=username,
                                   password=password,
                                   private_key=private_key,
                                   port=int(port),
                                   cnopts=cnopts)

        logger.info("Connected to sftp.")

    def close(self):
        # Best effort
        try:
            super(Sftp, self).close()
        except Exception as e:
            logger.exception(e)
