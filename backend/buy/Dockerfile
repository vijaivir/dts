FROM python:3.8

ADD buy.py .
ADD requirements.txt .

EXPOSE 8080

RUN pip install -r requirements.txt
RUN echo "INSIDE DOCKER FILE "

CMD ["python", "buy.py"]