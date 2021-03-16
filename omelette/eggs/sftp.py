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
                 host_fingerprint: Optional[str] = None, auth_timeout: Optional[int] = None, **kwargs):
        self._cnopts = pysftp.CnOpts()

        if private_key:
            private_key = pysftp.RSAKey.from_private_key(StringIO(private_key), passphrase)

        # Add host key when not on local, where it can be stored in /.ssh/known_hosts.
        if os.getenv("PROJECT_ENV", "local") != "local":
            fingerprint = host_fingerprint.encode()
            host_key = pysftp.RSAKey(data=decodebytes(fingerprint))
            self._cnopts.hostkeys.add(host, 'ssh-rsa', host_key)

        # starting point for transport.connect options
        self._host = host
        self._tconnect = {'username': username, 'password': password,
                          'hostkey': None, 'pkey': None}
        self._default_path = None

        # check that we have a hostkey to verify
        if self._cnopts.hostkeys is not None:
            self._tconnect['hostkey'] = self._cnopts.get_hostkey(host)

        self._sftp_live = False
        self._sftp = None
        self._set_username()
        self._set_logging()
        # Begin the SSH transport.
        self._transport = None
        self._start_transport(host, port)
        self._transport.use_compression(self._cnopts.compression)
        self._set_authentication(password, private_key, passphrase)
        self._transport.auth_timeout = auth_timeout or 30
        self._transport.connect(**self._tconnect)

        logger.info("Connected to sftp.")
