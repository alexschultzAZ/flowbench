# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# COPY --chown=app:app tmp/            /tmp/

# Install any needed packages
RUN pip install -r requirements.txt

ENV OUTPUTBUCKET stage1
ENV ENDPOINTINPUT 172.17.0.2:9000
ENV PUSHGATEWAY_IP 172.17.0.3:9091
ENV STORAGE_TYPE obj
ENV MN_FS false

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "index.py"]