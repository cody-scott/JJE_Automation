for local dev, use traefik and devcontainers in vs code to debug the app

traefik has a default https which is required to auth with yahoo

compose file should start the container, then connect to the container
alternative might be to set the network in a .devcontainer file


```
.env file

CLIENT_ID={yahoo client id}
CLIENT_SECRET={yahoo client secret}
DETA_PROJECT={deta project id}
SITE={site path - https://abc.abc.com}
```