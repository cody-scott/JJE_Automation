FROM python:alpine

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_DEBUG=1

WORKDIR app

COPY * /app/

RUN pip install -r requirements.txt

# RUN useradd appuser && chown -R appuser /app
# USER appuser

# CMD python main.py
CMD tail -f /dev/null # keep container running