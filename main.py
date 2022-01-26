from dataclasses import fields
from deta import Deta
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
import requests
import json
import os
import datetime

from Solver.solver import FantasyModel
from Solver import player_class
from PerformanceData.get_performance import performance_df, reduce_frame

load_dotenv()

deta_url = os.environ['DETA_URL']
deta_project = os.environ['DETA_PROJECT']


def get_ids(depth=2):
    print("Collecting Player ids")
    my_team = _get_my_team()
    fas = _get_fa(depth)
    return remove_duplicate_ids(my_team + fas)


def _get_fa(depth=2):
    r = []
    for _ in range(0, 25*depth, 25):
        data = requests.get(f"{deta_url}/players?start_num={_}").json()
        for p in data:
            if "G" in p['eligible_positions']['position']: continue
            f = dict(
                id=p['player_id'],
                name=p['name']['full'],
                positions=[_.replace("+", "") for _ in p['eligible_positions']['position'] if _ not in ['G', 'Util']]+["Bench"],
                current_position="Waivers",
                team=p['editorial_team_full_name']
            )
            r.append(f)
    return r


def _get_my_team():
    data = requests.get(f"{deta_url}/roster?team_id=8").json()
    r = []
    for p in data['players']['player']:
        if "G" in p['eligible_positions']['position']: continue
        f = dict(
            id=p['player_id'],
            name=p['name']['full'],
            positions=[_.replace("+", "") for _ in p['eligible_positions']['position'] if _ not in ['G', 'Util']]+["Bench"],
            current_position=p['selected_position']['position'].replace("BN", "Bench"),
            team=p['editorial_team_full_name']
        )
        r.append(f)
    return r


def remove_duplicate_ids(players):
    print('removing duplicates')
    out = []
    _ids = []
    for _ in players:
        if _['id'] not in _ids:
            _ids.append(_['id'])
            out.append(_) 
    return out


def build_player_classes(player_df):
    print("Building player class")
    dc_cols = [_.name for _ in fields(player_class.Player)]
    r_df = reduce_frame(player_df, _days=14)
    r_df = r_df[[_ for _ in r_df.columns if _ in dc_cols]]
    data = json.loads(r_df.reset_index().to_json(orient="records"))
    return [player_class.Player(**p) for p in data]


def main():
    # players = get_ids()
    # data = performance_df(players)
    # data.to_json('player_data.json', orient='records')
    
    data = pd.read_json('player_data.json')
    players = build_player_classes(data)

    model = build_team(players)

    save_to_deta(model.results_to_json())


def save_to_deta(result):
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    deta = Deta(deta_project)
    drive = deta.Drive("yahoo_results")
    drive.put(f'results_{dt}.json', result)

    with open(Path('results')/f"results_{dt}.json", "w") as f:
        json.dump(result, f, indent=4)


def build_team(players):
    solver = FantasyModel()
    players = player_class.join_protected(players, 'protected_players.json')
    solver.build_model(players)
    solver.solve_model()
    solver.print_solved(show_unplaced=False)
    return solver
    

if __name__ == "__main__":
    main()