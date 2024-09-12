# Use the official lightweight Python image.
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
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages including PyTorch
RUN python3 -m pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html

# Set up the application
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install Python dependencies
RUN python3 -m pip install flask gunicorn

# Expose the port your Python application runs on
EXPOSE 8080

# Command to run the Flask application with Gunicorn
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
