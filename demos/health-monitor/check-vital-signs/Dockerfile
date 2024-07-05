FROM ghcr.io/openfaas/classic-watchdog:0.2.1 as watchdog

FROM python:3.9-slim

RUN mkdir -p /home/app
# Set the working directory in the container

WORKDIR /home/app

# Install gcc and other dependencies
RUN apt-get update && apt-get install -y gcc g++ make

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .


COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog


# Populate example here - i.e. "cat", "sha512sum" or "node index.js"
ENV fprocess="python3 handler.py"
# Set to true to see request in function logs


EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]