from pathlib import Path
import json
import datetime
import requests
import pandas as pd 

from dataclasses import fields
from Solver.player_class import Player

def load_nhl_yahoo():
    """load the yahoo nhl lookup json file. Key is yahoo id, value contains {'nhl_id', 'name', 'yahoo_id'}"""
    p = Path('PerformanceData/yahoo_nhl.json')
    if not p.exists:
        p = Path('yahoo_nhl.json')
    txt = p.read_text()
    return json.loads(txt)


def process_game(game_data, player_dict):
    _stats = game_data['stat']
    _date = game_data['date']
    _date = datetime.datetime.strptime(_date, "%Y-%m-%d")

    _stats['date'] = _date

    _stats.update(player_dict)    

    return _stats


def process_player(player_data, player_dict):
    game_data = [process_game(_, player_dict) for _ in player_data['stats'][0]['splits']]
    return game_data


def get_data(player):
    # print(player['nhl_id'], player['name'])
    # {'yahoo_id': '4699', 'nhl_id': '8475184', 'name': 'Chris Kreider'}    
    data = requests.get(f"https://statsapi.web.nhl.com/api/v1/people/{player['nhl_id']}/stats/?stats=gameLog&season=20212022").json()
    return process_player(data, player)


def performance_df(player_ids):
    yahoo_nhl = load_nhl_yahoo()

    results = []
    for i, _ in enumerate(player_ids, 1):
        print(f"{i} of {len(player_ids)}", end="\r")
        yahoo_nhl_value = yahoo_nhl.get(_['id'])
        if yahoo_nhl_value is None: continue

        _.update(yahoo_nhl_value)
        results.append(get_data(_))
        

    df = pd.concat([
        pd.DataFrame.from_dict(_)
        for _ in results
    ]).fillna(0)
    return df


def reduce_frame(_df, _days=None):
    """this reduces the full list of games for the players down to a single row for the specified period"""
    _df = _df.copy()
    # _df['penaltyMinutes'] = _df['penaltyMinutes'].astype(int)
    _df['positions'] = _df['positions'].apply(lambda x: "|".join(x))
    if _days is None:
        _days = 14
    _id_df = _df[["id", "name", 'positions', 'current_position', 'team']].drop_duplicates().set_index("id")
    sum_df = _df.loc[_df['date'] >= datetime.datetime.today() - datetime.timedelta(days=_days)].groupby(
        "id").sum()
    new_df = _id_df.join(sum_df).fillna(0)
    new_df['positions'] = new_df['positions'].apply(lambda x: x.split("|"))
    return new_df
