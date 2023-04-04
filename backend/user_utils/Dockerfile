FROM python:3.9

WORKDIR /backend/user_utils

COPY ./user_utils/userutilsservice.py .
COPY ../requirements.txt .

RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED 1
EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:5000 userutilsservice:app