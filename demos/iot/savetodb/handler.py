import io
import json
from minio import Minio
from minio.error import S3Error

def handle(req):
    
    minio_client = Minio(
        "172.17.0.3:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

    try:
        # Parse the incoming request
        # temp_data = json.loads(req)
        temperature_object = minio_client.get_object("temperatures", "temperature.json")
        temperature_data = json.loads(temperature_object.read())
        # temperature_celsius = temperature_data["temperature_celsius"]
        temperature_fahrenheit = temperature_data["temperature_fahrenheit"]

        temp_data = {
            "temperature_fahrenheit": temperature_fahrenheit
        }
        temp_data_str = json.dumps(temp_data)
        minio_client.put_object(
          "output",
          "temperature.json",
          data=io.BytesIO(temp_data_str.encode('utf-8')),
          length=len(temp_data_str),
          content_type='application/json'
        )

        return json.dumps({"message": "Temperature saved successfully"})
    except S3Error as e:
        return f"Error saving temperature data: {str(e)}"
