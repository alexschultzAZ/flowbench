import io
import json
from minio import Minio
from minio.error import S3Error
import os

def handle(req):
    minio_addr = os.getenv('minio')
    print("env is " + minio_addr)

    minio_client = Minio(
        minio_addr,
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

    try:
        # Retrieve the temperature data from the "temperatures" bucket
        temperature_object = minio_client.get_object("temperatures", "temperature.json")
        temperature_data = json.loads(temperature_object.read())
        temperature_celsius = temperature_data["temperature_celsius"]

        # Convert Celsius to Fahrenheit
        temperature_fahrenheit = (temperature_celsius * 9/5) + 32
        temp_data = {
            "temperature_celsius": temperature_celsius,
            "temperature_fahrenheit": round(temperature_fahrenheit, 2)
        }
        temp_data_str = json.dumps(temp_data)
        minio_client.put_object(
          "temperatures",
          "temperature.json",
          data=io.BytesIO(temp_data_str.encode('utf-8')),
          length=len(temp_data_str),
          content_type='application/json'
        )

        return json.dumps(temp_data)
    except S3Error as e:
        return f"Error retrieving temperature data: {str(e)}"

res = handle("")
print(res)
