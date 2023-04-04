FROM python:3.9

WORKDIR /backend/sell

COPY ./sell/sellservice.py .
COPY ../requirements.txt .
COPY ../user_utils/userutilsservice.py .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:5000 sellservice:app