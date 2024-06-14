import io
import random
import json
from minio import Minio

def handle(req):
    print("hi")
    minio_client = Minio(
        "172.17.0.3:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    print(minio_client)

    # Generate a random temperature
    temperature = round(random.uniform(-20.0, 40.0), 2)
    temp_data = {"temperature_celsius": temperature}

    # Save the temperature to the "temperatures" bucket
    temp_data_str = json.dumps(temp_data)
    minio_client.put_object(
        "temperatures",
        "temperature.json",
        data=io.BytesIO(temp_data_str.encode('utf-8')),
        length=len(temp_data_str),
        content_type='application/json'
    )

    return json.dumps(temp_data)

handle("")