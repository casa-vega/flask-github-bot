FROM tiangolo/uwsgi-nginx-flask:python3.10

COPY ./app /app
RUN pip3 install -r /app/requirements.txt
