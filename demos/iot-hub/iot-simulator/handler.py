import os
import numpy as np
import pandas as pd
from minio import Minio
from minio.error import S3Error
import io
import random

def generate_sensor_data(minio_client, bucket_name):
    num_devices = 10  # Number of IoT devices
    data_size = 10 # Number of data points per device
    
    def generate_data_points():
        timestamps = pd.date_range(start=pd.Timestamp.now(), periods=data_size, freq='min')
        data = []
        for device_id in range(num_devices):
            for timestamp in timestamps:
                location = (random.uniform(-90, 90), random.uniform(-180, 180), random.uniform(0, 10000))
                temperature = random.uniform(-40, 50)
                moisture = random.uniform(0, 100)
                power_consumption = random.uniform(0, 1000)
                health_status = random.choice(['Good', 'Fair', 'Poor'])
                data.append([device_id, timestamp, *location, temperature, moisture, power_consumption, health_status])
        return pd.DataFrame(data, columns=['device_id', 'timestamp', 'latitude', 'longitude', 'elevation', 
                                           'temperature', 'moisture', 'power_consumption', 'health_status'])
    
    try:
        # Check if the object exists
        existing_data = None
        try:
            obj = minio_client.get_object(bucket_name, 'sensor_data.csv')
            existing_data = pd.read_csv(io.BytesIO(obj.read()))
        except S3Error as e:
            if e.code == 'NoSuchKey':
                print("No existing data found, creating a new CSV file.")
            else:
                raise e

        # Generate new data points
        new_data = generate_data_points()
        
        if existing_data is not None:
            combined_data = pd.concat([existing_data, new_data])
        else:
            combined_data = new_data
        
        csv_data = combined_data.to_csv(index=False)

        minio_client.put_object(bucket_name, 'sensor_data.csv', io.BytesIO(csv_data.encode('utf-8')), len(csv_data))
        print("Sensor data pushed to MinIO bucket successfully.")
    except S3Error as e:
        print("Error occurred while uploading to MinIO:", e)

# Environment Variables
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET')

# MinIO Client
minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

# Ensure bucket exists
if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
    minio_client.make_bucket(MINIO_BUCKET_NAME)

# Generate sensor data and push to MinIO
generate_sensor_data(minio_client, MINIO_BUCKET_NAME)
