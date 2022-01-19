import json
import requests
import xmltodict
import datetime
from aws_functions import upload_file, list_files


#------- function definitions --------

# uses yahoo app info and a passed in refresh token to retrieve and store updated tokens to creds.json
def _getNewAccessToken(refresh_token, config_file):

  url = "https://api.login.yahoo.com/oauth2/get_token"

  payload=f"client_id={config_file['client_id']}&client_secret={config_file['client_secret']}&redirect_uri=oob&refresh_token={refresh_token}&grant_type=refresh_token"
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
def validateAccessToken(config_file):
    with open('creds.json') as f:
        creds = json.loads(f.read())

    if datetime.datetime.utcnow() > datetime.datetime.strptime(creds['expires_in'],'%Y-%m-%d %H:%M:%S.%f'):
        print('Access token expired.')
        print('Getting new access token....')
        _getNewAccessToken(creds['refresh_token'],config_file)
        with open('creds.json') as f:
            creds = json.loads(f.read())
    else:
        print('Current access token still valid.')
    return creds

# Passes in yahoo game id, yahoo league id, and a valid creds.json object to get weekly scoreboard info
# Converts the xml response to json, creates and writes that response to a json file
# Returns the name of the newly created file for use in s3 copy to bucket
def getWeeklyScoreboard(game,league,week,auth):

    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{game}.l.{league}/scoreboard?week={week}"

    payload={}
    headers = {
    'Authorization': f"Bearer {auth['access_token']}"
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    response_json = xmltodict.parse(response.text)

    with open(f'weekly_scoreboard_data/{game}_{league}_week-{week}.json', 'w') as f:
        f.write(json.dumps(response_json))

    return f'weekly_scoreboard_data/{game}_{league}_week-{week}.json'

def _getCurrentWeek(game,league,auth):

    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{game}.l.{league}"

    payload={}
    headers = {
    'Authorization': f"Bearer {auth['access_token']}"
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    response_json = xmltodict.parse(response.text)

    return response_json['fantasy_content']['league']['current_week']


def calculateWeekToPull(bucket,prefix,creds):
    files = list_files(bucket,prefix)
    weeks = [int(i.split('.')[0].split('-')[-1]) for i in files]

    # set weeks to compare
    last_pulled_week = int(max(weeks))
    current_week = int(_getCurrentWeek(config['yahoo_game_id'],config['yahoo_league_id'],auth=creds))
    current_gap = current_week - last_pulled_week

    # identify week to pull, if data is not up to date
    if current_gap >= 2:
        week_to_pull = int(last_pulled_week+1)
        print(f'Currently {current_gap-1} full week(s) behind. Pulling week {week_to_pull} data...')
        return week_to_pull
    elif current_gap == 1:
        print(f'All full weeks have been pulled. Data is up to date. Wait until Monday to refresh.')
        return 0
    else:
        print(f'Current gap is {current_gap}. Something is wrong. Look at S3 bucket and current week setup.')
        return 0



#------- end defs -------

if __name__ == '__main__':

    #load in config.json
    with open('config.json') as f:
        config = json.loads(f.read())

    # get valid credentials for Yahoo API
    creds = validateAccessToken(config)
    
    # identify the week to pull
    week = calculateWeekToPull('basketball-data-store','yahoo-fantasy/weekly_scoreboard_data/',creds)

    if week != 0:
        # store scoreboard output into a json file, sets var to the json file name
        weekly_json_file = getWeeklyScoreboard(config['yahoo_game_id'],config['yahoo_league_id'],week=week,auth=creds)

        # copy the file to the s3 bucket
        print(upload_file(weekly_json_file,'basketball-data-store','yahoo-fantasy/'+weekly_json_file))