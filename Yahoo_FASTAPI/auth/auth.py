from fastapi import FastAPI, APIRouter
from starlette.middleware.sessions import SessionMiddleware

from starlette.requests import Request
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth

from starlette.responses import RedirectResponse

from auth import deta_utils
from dotenv import load_dotenv
import os
load_dotenv()

config = Config()
# config = Config('.env') if os.environ['LOCAL'] else Config()

oauth = OAuth(
    config, 
    fetch_token=deta_utils.load_token, 
    update_token=deta_utils.save_token
)
oauth.register(name='yahoo')

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.get("/")
async def reroute_login():
    rr = router.url_path_for('login_via_yahoo')
    response = RedirectResponse(url=rr)
    return response

@router.get("/login")
async def login_via_yahoo(request: Request):
    yahoo = oauth.create_client('yahoo')
    redirect_uri = request.url_for('auth_via_yahoo')
    # redirect_uri = redirect_uri.replace("http://", "https://")
    print(redirect_uri)
    return await oauth.yahoo.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_via_yahoo(request: Request):
    print('cb')
    token = await oauth.yahoo.authorize_access_token(request)
    deta_utils.save_token('yahoo', token)
    return {'yes'}
    return token

async def get_token():
    t = oauth.fetch_token()
    return t
