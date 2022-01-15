import json 
import os
from deta import Deta

from dotenv import load_dotenv
load_dotenv()

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
authorization_base_url = 'https://api.login.yahoo.com/oauth2/request_auth'
token_url = 'https://api.login.yahoo.com/oauth2/get_token'
SITE=os.environ['SITE']
local = os.environ.get('LOCAL', "")

LEAGUE_ID = os.environ.get('LEAGUE_ID')

deta = Deta(os.environ['DETA_PROJECT'])
drive = deta.Drive("yahoo")

def load_token():
    d = drive.get(f'{local}token.json')
    data = d.read()
    d.close()
    return json.loads(data)

def save_token(token):
    d = json.dumps(token, indent=4)
    drive.put(f'{local}token.json', d)
