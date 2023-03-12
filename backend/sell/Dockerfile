FROM python:3.8

ADD sell.py .
ADD requirements.txt .

EXPOSE 8080

RUN pip install -r requirements.txt

CMD ["python", "sell.py"]