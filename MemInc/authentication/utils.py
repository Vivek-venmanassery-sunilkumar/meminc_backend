# authentication/utils.py
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests


load_dotenv()

def verify_google_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), os.environ.get('GOOGLE_CLIENT_ID'))
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid issuer.')
        return idinfo
    except ValueError:
        return None