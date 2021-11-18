import json
import requests
import xmltodict
import datetime


#------- function definitions --------

# uses yahoo app info and a passed in refresh token to retrieve and store updated tokens to creds.json
def _getNewAccessToken(refresh_token):

  url = "https://api.login.yahoo.com/oauth2/get_token"

  payload=f"client_id={yahoo['client_id']}&client_secret={yahoo['client_secret']}&redirect_uri=oob&refresh_token={refresh_token}&grant_type=refresh_token"
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  response = requests.request("POST", url, headers=headers, data=payload)

  # truncate credentials file, update with new credentials, and replace expires_in seconds with the expiration timestamp
  with open('creds.json', 'w') as f:
    c = json.loads(response.text)
    c['expires_in'] = str(datetime.datetime.utcnow()+datetime.timedelta(0,int(c['expires_in'])))
    f.write(json.dumps(c))
  # print(c['expires_in'])
  # print(response.text)

# Checks if current access token still valid. If not valid, uses _getNewAccessToken to refresh the access token. Returns a set of valid credentials.
def validateAccessToken():
    with open('creds.json') as f:
        creds = json.loads(f.read())

    if datetime.datetime.utcnow() > datetime.datetime.strptime(creds['expires_in'],'%Y-%m-%d %H:%M:%S.%f'):
        print('Access token expired.')
        print('Getting new access token....')
        _getNewAccessToken(creds['refresh_token'])
        with open('creds.json') as f:
            creds = json.loads(f.read())
    else:
        print('Current access token still valid')
    return creds

# Passes in yahoo game id, yahoo league id, and a valid creds.json object to return weekly scoreboard info
def getWeeklyScoreboard(game,league,auth):

    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{game}.l.{league}/scoreboard"

    payload={}
    headers = {
    'Authorization': f"Bearer {auth['access_token']}"
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    response_json = xmltodict.parse(response.text)

    with open('response.json', 'x') as f:
        f.write(json.dumps(response_json))

#------- end defs -------

if __name__ == '__main__':

    # grabs stored yahoo application info (client id and client secret) - needed for getting a new access token
    with open('yahoo_app.json') as f:
        yahoo = json.loads(f.read())

    # set your game id and league id to access (yahoo specific)
    # currently set for NBA 2021
    yahoo_game = '410'
    yahoo_league = '43952'

    # get valid credentials for Yahoo API
    creds = validateAccessToken()

    getWeeklyScoreboard(yahoo_game,yahoo_league,auth=creds)