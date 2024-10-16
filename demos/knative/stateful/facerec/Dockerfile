# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    libsm6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libxext6 \
    ca-certificates


WORKDIR /app

RUN python3 -m pip install torch==1.9.0+cpu torchvision==0.10.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
ADD requirements.txt /app

RUN pip install -r requirements.txt

ADD . /app

ENV OUTPUTBUCKET="stage4"
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
