# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

ADD requirements.txt /app

# Install any needed packages
RUN pip install -r requirements.txt

ADD . /app
# ENV NEXT_URL="http://kn-modect.default.svc.cluster.local"
ENV OUTPUTBUCKET="stage1"
ENV STORAGE_TYPE="obj"
ENV ENDPOINTINPUT="172.17.0.3:9000"
ENV PUSHGATEWAY_IP="172.17.0.2:9091"
ENV MN_FS="true"
ENV ACCELERATION="cpu"

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "index.py"]