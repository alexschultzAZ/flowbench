FROM  ghcr.io/openfaas/classic-watchdog:0.2.1 as watchdog
FROM python:3.7

# Allows you to add additional packages via build-arg
ARG ADDITIONAL_PACKAGE

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog
RUN apt-get update \
    && apt-get install -y ca-certificates libsm6 libxext6 libgl1-mesa-glx libglib2.0-0 ${ADDITIONAL_PACKAGE} \
    && rm -rf /var/lib/apt/lists/

# Add non root user
RUN groupadd app && useradd -r -g app app

WORKDIR /home/app/

COPY index.py           .
COPY requirements.txt   .

RUN chown -R app /home/app && \
    mkdir -p /home/app/python && chown -R app /home/app
USER app
ENV PATH=$PATH:/home/app/.local/bin:/home/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/home/app/python
ENV ENDPOINTINPUT=172.0.
ENV OUTPUTBUCKET1=stage1
ENV OUTPUTBUCKET2=stage2
ENV OUTPUTBUCKET3=stage3
ENV OUTPUTBUCKET4=stage4
ENV PIPELINE_STAGE=2
ENV MODECT_MIN_AREA=5
ENV MODECT_SKIP_RATE=1
ENV STORAGE_TYPE=local_storage
ENV MOUNT_PATH=/mnt/local-storage
RUN pip install -r requirements.txt --target=/home/app/python

RUN mkdir -p function
RUN touch ./function/__init__.py

WORKDIR /home/app/function/

WORKDIR /home/app/

USER root

COPY function           function

# Allow any user-id for OpenShift users.
RUN chown -R app:app ./ && \
    chmod -R 777 /home/app/python

USER app

ENV fprocess="python3 index.py"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]