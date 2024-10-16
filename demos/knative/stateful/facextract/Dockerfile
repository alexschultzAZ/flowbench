FROM python:3.9-slim

WORKDIR /app

ADD requirements.txt /app/


RUN pip install -r requirements.txt

ADD . /app



# ENV NEXT_URL="http://facextract.default.svc.cluster.local"
ENV OUTPUTBUCKET="stage2"
ENV STORAGE_TYPE="obj"
ENV ENDPOINTINPUT="172.17.0.3:9000"
ENV PUSHGATEWAY_IP="172.17.0.2:9091"
ENV PIPELINE_STAGE="2"
ENV MODECT_MIN_AREA="5"
ENV MODECT_SKIP_RATE="1"
ENV MN_FS="true"
ENV ACCELERATION="cpu"

EXPOSE 8080

CMD ["python", "index.py"]