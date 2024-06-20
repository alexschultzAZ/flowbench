FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y ffmpeg

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "handler.py"]
