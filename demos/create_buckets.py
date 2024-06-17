from minio import Minio
from minio.error import S3Error
import os

minio_addr = os.getenv('minio')
print("env is " + os.getenv('test'))
minio_client = Minio(
	minio_addr,
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
)

buckets_to_create = ["temperatures", "output"]
for bucket_name in buckets_to_create:
	if not minio_client.bucket_exists(bucket_name):
		minio_client.make_bucket(bucket_name)
	else:
		print("Bucket {} already exists".format(bucket_name))
