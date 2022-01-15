from requests_oauthlib import OAuth2Session

from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
import os
import json
from bs4 import BeautifulSoup

from utils import load_token, save_token, client_id, client_secret, authorization_base_url, token_url, SITE

from yahoo import request_teams, request_players, request_standings, request_roster, process_request, process_current_positions



app = Flask(__name__)
app.secret_key = 'the random string'

@app.route('/')
def index():
    return "hi there"

@app.route('/teams')
def teams():
    t = request_teams()['results']
    return jsonify(t.text)
    return jsonify(process_request(t))


@app.route('/myteam')
def myteam():
    t = request_roster(8)['results']
    raw = request.args.get('raw')
    if raw is not None: 
        return jsonify(t.text)
    else:
        return jsonify(process_current_positions(t))

# @app.route('/current-positions')
# def current_roster_positions():
#     t = request_roster(8)['results']
#     raw = request.args.get('raw')
#     if raw is not None: 
#         return jsonify(t.text)
#     else:
#         return jsonify(process_current_positions(t))

@app.route('/players')
def players():
    start_num = request.args.get('start')
    data = {
            'status': "W",
            "sort_type": "lastweek",
            "sort": "AR",
        }
    if start_num is not None:
        data['start'] = start_num
    t = process_request(request_players(data)['results'])
    return jsonify(t)
    

@app.route("/login")
def login():
    # return "login"
    github = OAuth2Session(
        client_id, 
        redirect_uri=f'{SITE}/callback',
        state=None,
        token=None
    )
    authorization_url, state = github.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    # return "callback"
    github = OAuth2Session(client_id, redirect_uri=f'{SITE}/callback', state=session['oauth_state'])
    token = github.fetch_token(
        token_url, 
        client_secret=client_secret,
        authorization_response=request.url
    )
    session['oauth_token'] = token
    save_token(token)
    return token
    
@app.route("/refresh")
def refresh_user_token():
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


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
    app.run(debug = True, host = '0.0.0.0')
