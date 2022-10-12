import os
import json
import requests
import datetime
from aws_functions import update_secret, get_secret

# uses yahoo app info and a passed in refresh token to retrieve and store updated tokens to creds.json
def _getNewAccessToken(refresh_token):

  client_id = os.environ['YAHOO_CLIENT_ID']
  client_secret = os.environ['YAHOO_CLIENT_SECRET']
  url = "https://api.login.yahoo.com/oauth2/get_token"

  payload=f"client_id={client_id}&client_secret={client_secret}&redirect_uri=oob&refresh_token={refresh_token}&grant_type=refresh_token"
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  response = requests.request("POST", url, headers=headers, data=payload)

  # truncate credentials secret, update with new secret, and replace expires_in seconds with the expiration timestamp
  new_creds = json.loads(response.text)
  new_creds['expires_in'] = str(datetime.datetime.utcnow()+datetime.timedelta(0,int(new_creds['expires_in'])))

  response = update_secret(json.dumps(new_creds))

  return response

# Checks if current access token still valid. If not valid, uses _getNewAccessToken to refresh the access token. Returns a set of valid credentials.
def validateAccessToken():
    creds = get_secret()

    if datetime.datetime.utcnow() > datetime.datetime.strptime(creds['expires_in'],'%Y-%m-%d %H:%M:%S.%f'):
        print('Access token expired.')
        print('Getting new access token....')
        _getNewAccessToken(creds['refresh_token'])
    else:
        print('Current access token still valid.')
    return creds