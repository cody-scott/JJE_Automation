from utils import load_token, save_token, client_id, client_secret, authorization_base_url, token_url
from utils import LEAGUE_ID, SITE
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode
from bs4 import BeautifulSoup

def refresh_tk():
    token = load_token()
    extra = {
        'client_id': client_id,
        'client_secret': client_secret,
    }

    oauth = OAuth2Session(client_id, redirect_uri=f'{SITE}/callback')
    new_token = oauth.refresh_token(
        token_url,
        refresh_token=token['refresh_token'],
        **extra
    )

    save_token(new_token)
    return new_token  

def create_session():
    tk = refresh_tk()
    
    return OAuth2Session(
        client_id=client_id,
        redirect_uri=f'{SITE}/callback',
        state=None,
        token=tk
    )

def request_teams(use_login=False):
    yahoo_obj = create_session()
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_ID}/teams"
    if use_login:
        url += ';use_login=1'
    return _get_request(yahoo_obj, url)

def request_standings():
    yahoo_obj = create_session()
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_ID}/standings"
    return _get_request(yahoo_obj, url)

def request_roster(team_id):
    yahoo_obj = create_session()
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{LEAGUE_ID}.t.{team_id}/roster/players"
    return _get_request(yahoo_obj, url)

def request_players(player_dict):
    yahoo_obj = create_session()
    player_args = urlencode(player_dict)
    player_args = player_args.replace("&", ";")
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_ID}/players;{player_args}/stats"
    return _get_request(yahoo_obj, url)

def request_player(player_id, sub_resources=None):
    yahoo_obj = create_session()
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_ID}/players;player_keys=nhl.p.{player_id}/stats"
    if sub_resources is not None:
        sr = urlencode(sub_resources)
        sr = sr.replace("&", ";")
        url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_ID}/players;player_keys=nhl.p.{player_id};{sr}/stats"
    return _get_request(yahoo_obj, url)

def _get_request(yahoo_obj, url):
    result = yahoo_obj.get(url)
    results, status_code = result.text, result.status_code

    return {"results": result, "status_code": status_code}


def process_request(r):
    soup = BeautifulSoup(r.text.replace("\\n", "\n"), 'html.parser')

    players = []
    for player in soup.find('players').find_all('player'):
        _id = get_number_or_none(player, 'player_id')
        _name = get_value_or_none(player, 'full')
        _positions = get_positions(player)
        tn = get_value_or_none(player, "editorial_team_full_name")
        # players.append([_id, _name, ",".join(_positions), tn])
        players.append(dict(
            id=_id, 
            name=_name,
            positions=",".join(_positions),
            team=tn
        ))

    return players


def process_current_positions(r):
    soup = BeautifulSoup(r.text.replace("\\n", "\n"), 'html.parser')

    players = []
    for player in soup.find('players').find_all('player'):
        _id = get_number_or_none(player, 'player_id')
        _name = get_value_or_none(player, 'full')
        _positions = get_positions(player)
        _sel_positions = player.find('selected_position').find('position').text
        _sel_positions = _sel_positions.replace("+", "")
        tn = get_value_or_none(player, "editorial_team_full_name")
        players.append(dict(
            id=_id, 
            name=_name,
            positions=",".join(_positions),
            current_position=_sel_positions,
            team=tn
        ))
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