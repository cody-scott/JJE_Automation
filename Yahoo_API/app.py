from main import app
import os

if __name__ == "__main___":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
    app.run(debug = True, host = '0.0.0.0')