from deta import Deta
from dotenv import load_dotenv

import os
import json
load_dotenv()

deta = Deta(os.environ['DETA_PROJECT'])
drive = deta.Drive("yahoo")
local = os.environ.get('LOCAL', "")

def load_token():
    try:
        d = drive.get(f'{local}token_f.json')
        data = d.read()
        d.close()
        return json.loads(data)
    except:
        return None

def save_token(provider, token, *args, **kwargs):
    d = json.dumps(token, indent=4)
    drive.put(f'{local}token_f.json', d)
    return token
