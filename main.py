import requests
import json
import os
from pathlib import Path
import datetime

from PerformanceData import process
from Solver.solver import FantasyModel
from Solver import player_class

from dotenv import load_dotenv
load_dotenv()

deta_url = os.environ['DETA_URL']

def get_ids():
    my_team = requests.get(f"{deta_url}/myteam").json()
    i = 25
    fas = []
    for _ in range(0, i*2, i):
        f = requests.get(f"{deta_url}/players?start={_}")
        fas += f.json()
    players = my_team + fas
    players = remove_duplicate_ids(players)
    return [_ for _ in players if 'G' not in _['positions']]

def remove_duplicate_ids(players):
    out = []
    _ids = []
    for _ in players:
        if _['id'] not in _ids:
            _ids.append(_['id'])
            out.append(_) 
    return out

def combine_data(player_data, data):
    data = json.loads(data.reset_index().to_json(orient="records"))
    # player_data = [{'id': _[0], 'name':_[1], 'positions':_[2].split(","), 'team': _[3]} for _ in players]
    for player in player_data:
        for _ in data:
            if _['id'] == player['id']:
                player.update(_)
    return [player_class.Player(**p) for p in player_data]


def main():
    players = get_ids()
    data = process.performance_data(players)
    data.to_csv('player_data.csv')
    # data = pd.read_csv('player_data.csv', low_memory=False).set_index('id')
    data = combine_data(players, data)
    build_team(data)

def save_to_deta(result):
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    deta = Deta(os.environ['DETA_PROJECT'])
    drive = deta.Drive("yahoo_results")
    drive.put(f'results_{dt}.json', results)

def build_team(players):
    solver = FantasyModel()
    players = player_class.join_protected(players, 'protected_players.json')
    solver.build_model(players)
    solver.solve_model()
    solver.print_solved(show_unplaced=False)
    save_to_deta(
        solver.results_to_json(Path('results'))
    )
    


if __name__ == "__main__":
    main()