import io
import os
import numpy as np
import json
from minio import Minio

# MinIO client setup


# def generate_sample_data():
#     # Generate sample data similar to heart disease dataset
#     sample = {
#         'age': np.random.randint(29, 77),
#         'sex': np.random.randint(0, 2),
#         'cp': np.random.randint(0, 4),
#         'trestbps': np.random.randint(94, 200),
#         'chol': np.random.randint(126, 564),
#         'fbs': np.random.randint(0, 2),
#         'restecg': np.random.randint(0, 2),
#         'thalach': np.random.randint(71, 202),
#         'exang': np.random.randint(0, 2),
#         'oldpeak': np.random.uniform(0, 6.2),
#         'slope': np.random.randint(0, 3),
#         'ca': np.random.randint(0, 4),
#         'thal': np.random.randint(1, 4)
#     }
#     return sample

def handle(req):
    minio_client = Minio(
        '172.17.0.3:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False
    )
    sample = {
        'age': np.random.randint(29, 77),
        'sex': np.random.randint(0, 2),
        'cp': np.random.randint(0, 4),
        'trestbps': np.random.randint(94, 200),
        'chol': np.random.randint(126, 564),
        'fbs': np.random.randint(0, 2),
        'restecg': np.random.randint(0, 2),
        'thalach': np.random.randint(71, 202),
        'exang': np.random.randint(0, 2),
        'oldpeak': np.random.uniform(0, 6.2),
        'slope': np.random.randint(0, 3),
        'ca': np.random.randint(0, 4),
        'thal': np.random.randint(1, 4)
    }
    # try:
    output_bucket = os.getenv('HEART_DATA')
    # Check if the bucket exists, create if it does not
    if not minio_client.bucket_exists(output_bucket):
        minio_client.make_bucket(output_bucket)
    
    # Generate sample data
    sample_data = sample
    
    # Convert to JSON
    json_data = json.dumps(sample_data)
    
    # Upload to MinIO, overriding the existing file
    minio_client.put_object(
        bucket_name=output_bucket,
        object_name='data.json',
        data=io.BytesIO(json_data.encode('utf-8')),
        length=len(json_data),
        content_type='application/json'
    )
    
    return json.dumps({'status': 'success', 'file_name': 'data.json', 'data': json_data})
    # except Exception as e:
    #     return e

result = handle('')
print(result)