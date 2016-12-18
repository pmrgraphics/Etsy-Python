import base64, os, pickle
from sys import argv
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

script, enc_file, password = argv


def decrypt(enc_file, password): 
  """
  Decrypts the credential file listed by using the password specified when
  creating the file.

  Args:
    enc_file: file name of credentials file
    password: passused when credentials file was created

  Returns:
    Dictionary containing authentication tokens for use

  """
  with open(enc_file, 'rb') as fp:
    enc_contents = pickle.load(fp)

  salt = enc_contents['Random']

  enc_token = enc_contents['Data']

  kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                 length=32, salt=salt,
                 iterations=500000,
                 backend=default_backend()
                )

  key = base64.urlsafe_b64encode(kdf.derive(password))

  fcrypto = Fernet(key)
  creds_decrypted = fcrypto.decrypt(enc_token)

  with open(creds_decrypted, 'rb') as fpp:
    creds = pickle.load(fp)
  consumer_key = creds['client_key']
  client_secret = creds['client_secret']
  oauth_token = creds['oauth_token']
  oauth_token_secret = creds['oauth_token_secret']
  return creds
