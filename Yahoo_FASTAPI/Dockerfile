# FROM python:alpine

# EXPOSE 5000

# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_DEBUG=1

# WORKDIR app

# COPY * /app/

# RUN apk update && apk add python3-dev \
#                           gcc \
#                           libc-dev \
#                           libffi-dev \
#                           musl-dev
# RUN pip install --upgrade pip setuptools-scm

# RUN pip install -r requirements.txt

# # RUN useradd appuser && chown -R appuser /app
# # USER appuser

# # CMD python main.py
# CMD tail -f /dev/null # keep container running

# FROM tiangolo/uvicorn-gunicorn:python3.9

# COPY requirements.txt /tmp/requirements.txt
# RUN pip install --no-cache-dir -r /tmp/requirements.txt

# COPY * /app/

FROM python:3.9
EXPOSE 8000
EXPOSE 80

WORKDIR /app/

COPY * /app/
RUN pip install -r requirements.txt
CMD tail -f /dev/null # keep container running