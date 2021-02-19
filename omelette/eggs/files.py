import gnupg
import logging

logger = logging.getLogger(__name__)


class FileDecryptError(Exception):
    pass


class Files:
    @classmethod
    def read_file_to_str(cls, file_path):
        logger.info(f"Reading file to string: {file_path}")
        with open(file_path, 'r') as f:
            return f.read()

    @classmethod
    def decrypt_pgp(cls, input_filepath: str, output_filepath: str, private_key: str, passphrase: str) -> str:
        """Decrypt PGP file using private key and passphrase."""
        gpg = gnupg.GPG()
        gpg.import_keys(private_key)

        with open(input_filepath, "rb") as encrypted_f:
            logger.info(f"Decrypting file: {input_filepath}")
            result = gpg.decrypt_file(encrypted_f,
                                      passphrase=passphrase,
                                      output=output_filepath,
                                      extra_args=["--ignore-mdc-error"])
            if result.ok:
                logger.info(f"File decryption successful. Decrypted file: {output_filepath}")
                return output_filepath
            else:
                raise FileDecryptError(result.stderr)

    @classmethod
    def encrypt_pgp(cls, input_filepath: str, output_filepath: str, public_key: str) -> str:
        """Encrypt PGP file using public key."""
        gpg = gnupg.GPG()
        key = gpg.import_keys(public_key)

        recipient = key.results[0]["fingerprint"]

        with open(input_filepath, "rb") as f:
            logger.info(f"Encrypting file: {input_filepath}")
            result = gpg.encrypt_file(file=f, recipients=[recipient], output=output_filepath, always_trust=True)
            if result.ok:
                logger.info(f"File encryption successful. Encrypted file: {output_filepath}")
                return output_filepath
            else:
                raise FileDecryptError(result.stderr)
