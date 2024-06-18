FROM  ghcr.io/openfaas/classic-watchdog:0.2.1 as watchdog
#FROM python:3.8-slim
FROM ubuntu:20.04

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

RUN apt-get update && apt-get install -y cmake ca-certificates libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6
RUN apt update -y; apt install -y \
        git \
        cmake \
        libsm6 \
        python3 \
        python3-pip
RUN python3 -m pip install torch==1.9.0+cpu torchvision==0.10.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN groupadd app && useradd -r -g app app

WORKDIR /home/app/
COPY requirements.txt   .

RUN chown -R app /home/app && \
    mkdir -p /home/app/python && chown -R app /home/app
USER app
ENV PATH=$PATH:/home/app/.local/bin:/home/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/home/app/python

RUN python3 -m pip install -r requirements.txt

RUN mkdir -p function
#COPY requirements/ function/
RUN touch ./function/__init__.py

WORKDIR /home/app/function/
COPY function/requirements.txt   .


USER root

#RUN mkdir =p /tmp/.cache
#ENV TORCH_HOME=/tmp/.cache/torch
#ENV XDG_CACHE_HOME=/tmp/.cache/torch

RUN chown -R app:app ./ && \
    chmod -R 777 /home/app/python

WORKDIR /home/app/

USER root

COPY --chown=app:app tmp/            /tmp/
COPY --chown=app:app function           function
COPY --chown=app:app index.py           .
COPY --chown=app:app handler1.py           .
COPY --chown=app:app requirements.txt           .

USER app
ENV fprocess="python3 index.py"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]
