from audioop import add
from fastapi import Depends, FastAPI
from starlette.middleware.sessions import SessionMiddleware

from auth.auth import router as auth_router
from auth.auth import oauth, get_token

from typing import Optional
from urllib.parse import urlencode
import xmltodict
from models import team_model, player_model
import models

from dotenv import load_dotenv
import os

import json
from pathlib import Path

import datetime

load_dotenv()
league_id = os.environ['LEAGUE_ID']
base_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}"

app = FastAPI(
    tags=['yahoo']
)
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
async def yahoo_players(status: str="W", sort_type: str="lastweek", sort: str="AR", start_num: Optional[int]=0, search: Optional[str]=None, count: Optional[int]=None):
    data = {
                'status': status,
                "sort_type": sort_type,
                "sort": sort,
                "start": start_num,
                "search": search,
                "count": count
    }

    data = {
        _: val for _ in data if (val := data[_]) is not None
    }
    # if start_num is not None:
    #     data['start'] = start_num

    player_args = urlencode(data)
    player_args = player_args.replace("&", ";")
    url = f"{base_url}/players;{player_args}/stats"
    token = await get_token()

    print(url)
    r = await oauth.yahoo.get(
        url,
        token=token
    )
    # print(r.content)
    
    rf = xmltodict.parse(r.content)['fantasy_content']['league']['players']['player']
    return rf


@app.get('/roster', response_model=models.RosterModel)
async def get_roster(team_id: int, roster_date: Optional[datetime.date]=None):
    token = await get_token()
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{league_id}.t.{team_id}/roster"
    
    if roster_date is not None:
        date_str = roster_date.strftime("%Y-%m-%d")
        url += f";date={date_str}"
    print(url)
    r = await oauth.yahoo.get(
        url,
        token=token
    )
    rf = xmltodict.parse(r.content)['fantasy_content']['team']['roster']
    return rf

@app.post('/transaction')
async def post_changes(team_id: int, add_player_id: Optional[int]=None, drop_player_id: Optional[int]=None):
    if all([add_player_id, drop_player_id]):
        _tp = "add/drop"
    elif add_player_id is not None:
        _tp = "add"
    elif drop_player_id is not None:
        _tp = "drop"
    else:
        return "Error!"

    _aa = format_player_xml(team_id, add_player_id, "add") if add_player_id is not None else ""
    _dd = format_player_xml(team_id, drop_player_id, "drop") if drop_player_id is not None else ""
    
    xml_data = f"""<?xml version='1.0'?>
                <fantasy_content>
                    <transaction>
                        <type>{_tp}</type>
                        <players>
                        {_aa}
                        {_dd}
                        </players>
                    </transaction>
                </fantasy_content>"""


    _url = "https://fantasysports.yahooapis.com/fantasy/v2/league/transactions"
    return xml_data

def format_player_xml(team_id: int, player_id: int, add_drop: str):
    return f"""<player>
                    <player_key>nhl.p.{player_id}</player_key>
                    <transaction_data>
                    <type>{add_drop}</type>
                    <destination_team_key>nhl.l.{league_id}.t.{team_id}</destination_team_key>
                    </transaction_data>
                </player>"""