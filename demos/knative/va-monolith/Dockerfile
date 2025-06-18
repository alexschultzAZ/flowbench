FROM python:3.9-slim

WORKDIR /app

ADD requirements.txt /app

RUN pip install -r requirements.txt

ADD . /app


EXPOSE 8080

CMD ["python", "index.py"]