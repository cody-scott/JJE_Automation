from pathlib import Path
import json
import datetime
import requests
import pandas as pd 

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
        print(f"{i} of {len(player_ids)}")
        _current = _
        yahoo_nhl_value = yahoo_nhl.get(_['id'])
        if yahoo_nhl_value is None: continue
        results.append(get_data(yahoo_nhl_value))
        

    df = pd.concat([
        pd.DataFrame.from_dict(_)
        for _ in results
    ]).fillna(0)
    return df
