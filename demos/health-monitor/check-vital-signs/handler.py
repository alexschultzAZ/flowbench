import json
import os
import numpy as np
import pandas as pd
from minio import Minio
import joblib  # for loading the model (older scikit-learn versions)

# MinIO client setup
minio_client = Minio(
    os.getenv('MINIO_ADDR'),
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)

# Load the logistic regression model from the .pkl file
def load_model():
    model_bucket = os.getenv('MODEL_BUCKET')
    model_filename = os.getenv('MODEL_FILENAME')

    # print('Model bucket is {}, filename = {}, minio = {}'.format(model_bucket, model_filename, minio_client._base_url._url))
    local_model_path = '/tmp/' + model_filename
    
    # Download model file from MinIO
    minio_client.fget_object(model_bucket, model_filename, local_model_path)
    
    # Load the model
    model = joblib.load(local_model_path)
    
    # Clean up downloaded file if needed
    os.remove(local_model_path)
    
    return model

# Function to handle incoming requests
def handle(req):
    try:
        # Load the model
        model = load_model()

        # Fetch the latest data from MinIO
        bucket_name = os.getenv('HEART_DATA')
        response = minio_client.get_object(bucket_name, 'data.json')
        json_data = response.data.decode('utf-8')

        # Convert JSON data to DataFrame
        data = json.loads(json_data)
        df = pd.DataFrame([data])

        # Make predictions
        predictions = model.predict(df)

        # Determine result
        result = "heart_attack" if predictions[0] == 1 else "no_heart_attack"

        return result

    except Exception as e:
        return str(e)


