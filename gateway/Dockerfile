FROM python:3.10-slim-buster as base

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .


RUN chmod +x install_openfaas_docker.sh

# RUN yes | ./install_openfaas_docker.sh

ENTRYPOINT [ "/install_openfaas_docker.sh" ]

EXPOSE 5000
EXPOSE 5678

# Debug Image
FROM base as debug

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

CMD [ "python3", "-m" , "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "flask", "run", "--host=0.0.0.0", "--no-debugger", "--no-reload"]


# Prod image
FROM base as prod

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
