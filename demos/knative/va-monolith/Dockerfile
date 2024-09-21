FROM python:3.9-slim

WORKDIR /app

COPY . /app


RUN pip install -r requirements.txt

ENV OUTPUTBUCKET stage3
ENV ENDPOINTINPUT 172.17.0.2:9000
ENV PUSHGATEWAY_IP 172.17.0.3:9091
ENV STORAGE_TYPE obj
ENV MN_FS false

EXPOSE 8080

CMD ["python", "index.py"]