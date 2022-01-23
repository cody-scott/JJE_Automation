from fastapi import Depends, FastAPI
from starlette.middleware.sessions import SessionMiddleware

from auth.auth import router as auth_router
from auth.auth import oauth, get_token

from typing import Optional
from urllib.parse import urlencode
import xmltodict
from models import team_model, player_model

from dotenv import load_dotenv
import os
load_dotenv()
league_id = os.environ['LEAGUE_ID']
base_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="some-random-string")

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


@app.get('/teams', response_model=team_model.TeamsModel)
async def yahoo_teams():
    token = await get_token()
    r = await oauth.yahoo.get(
        f'{base_url}/teams',
        token=token
    )
    rf = xmltodict.parse(r.content)['fantasy_content']['league']['teams']['team']
    return rf

@app.get('/players', response_model=player_model.PlayersModel)
async def yahoo_players(start_num: Optional[int]=0):
    data = {
                'status': "W",
                "sort_type": "lastweek",
                "sort": "AR",
    }
    if start_num is not None:
        data['start'] = start_num

    player_args = urlencode(data)
    player_args = player_args.replace("&", ";")
    url = f"{base_url}/players;{player_args}/stats"
    token = await get_token()

    r = await oauth.yahoo.get(
        url,
        token=token
    )
    rf = xmltodict.parse(r.content)['fantasy_content']['league']['players']['player']
    return rf
