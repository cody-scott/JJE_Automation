import requests
from bs4 import BeautifulSoup
import os

from _team_list_class import TeamList
from _team_combinations import team_from_list
from _protected_lists import rookies, goalies, bench_goalies


def player_list():
    # get my players
    print("loading player info")
    all_players, current_roster = get_current_roster()
    current_roster_class = team_from_list(current_roster)

    # this is list of players to check mixes of. Remove goalies and rookies from combinations
    _check_players = [p for p in all_players if p[0] not in [x[0] for x in rookies + goalies + bench_goalies]]
    _check_player_ids = [p[0] for p in _check_players]

    # get list of free agents
    _free_agents = [f for f in process_FA() for z in f[-1].split(",") if z not in ["G", "IR", "C"]]
    _free_agents_id = [f[0] for f in _free_agents]

    full_player_list = []
    ix = []
    for i in all_players + _free_agents:
        if i[0] not in ix:
            ix.append(i[0])
            full_player_list.append(i)

    # check players is my current team.
    # if i come up with a new permutation that works better i could just feed that in as the input
    # if a team combo has a free agent as the best option, then re run this using that player as the input
    tmp_ls = []
    for p in _free_agents:
        tmp_ls.append(_check_players + [p])
    print('')
    return {
        'all_players': all_players, 'current_roster_class': current_roster_class,
        'check_players': _check_players, 'free_agents': _free_agents,
        'full_player_list': full_player_list, 'team_list': tmp_ls,
        'original_roster_class': current_roster_class
    }


def get_current_roster():
    r = _request_roster()
    players = process_request(r)
    c_r = process_current_positions(r)
    return players, c_r


def _request_roster():
    headers = {
        'Authorization': "Token 9007e963847a704cdb85684228924fa457ea5bf5"
    }
    base_url = 'https://jje-league.herokuapp.com/'
    url = os.path.join(base_url, 'oauth/api/getroster/')

    r = requests.get(url, headers=headers, params={"team_id": 9})

    return r


def _request_FA_players(data=None, start_num=None):
    headers = {
        'Authorization': "Token 9007e963847a704cdb85684228924fa457ea5bf5"
    }
    base_url = 'https://jje-league.herokuapp.com/'
    url = os.path.join(base_url, 'oauth/api/searchplayers/')
    if data is None:
        data = {
            'status': "FA",
            "sort_type": "lastweek",
            "sort": "AR",
        }
    if start_num is not None:
        data['start'] = start_num

    r = requests.get(url, headers=headers, params=data)
    return r


def process_FA(data=None, start_num=None):
    _fa = _request_FA_players(data, start_num)
    return process_request(_fa)


def process_request(r):
    soup = BeautifulSoup(r.text.replace("\\n", "\n"), 'html.parser')

    players = []
    for player in soup.find('players').find_all('player'):
        _id = get_number_or_none(player, 'player_id')
        _name = get_value_or_none(player, 'full')
        _positions = get_positions(player)
        players.append([_id, _name, ",".join(_positions)])
    return players


def process_current_positions(r):
    soup = BeautifulSoup(r.text.replace("\\n", "\n"), 'html.parser')

    players = []
    for player in soup.find('players').find_all('player'):
        _id = get_number_or_none(player, 'player_id')
        _name = get_value_or_none(player, 'full')
        _positions = player.find('selected_position').find('position').text
        _positions = _positions.replace("+", "")
        players.append([_id, _name, _positions])
    return players


def get_value_or_none(_soup, val):
    try:
        return _soup.find(val).text
    except:
        return None


def get_number_or_none(_soup, val, num_type=None):
    if num_type is None:
        num_type = int
    try:
        return num_type(get_value_or_none(_soup, val))
    except:
        return None


def get_positions(_soup):
    ep = _soup.find('eligible_positions')
    if ep is None:
        return []
    return [v.text.replace("+", "") for v in ep.find_all('position') if v.text not in ['Util']]
