import os
import sys
import time
import shutil
from minio import Minio
from minio.error import InvalidResponseError
from datetime import datetime
from .handler1 import *
import ast

MINIO_ADDRESS = "172.17.0.2:9000"
minio_client = Minio(
    MINIO_ADDRESS,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def load_from_minio(bucket, file):
    try:
        new_file = "/tmp/" + file
        minio_client.fget_object(bucket, file, new_file)
        return new_file
    except InvalidResponseError as err:
        print(err)

def store_to_minio(bucket, ret):
    files = os.listdir(ret)
    if len(files) == 0:
        return

    # Put an object.
    try:
        os.chdir(ret)
        for file in files:
            minio_client.fput_object(bucket, file, file)
        return
    except InvalidResponseError as err:
        print(err)

def get_stdin():
    buf = ""
    while(True):
        line = sys.stdin.readline()
        buf += line
        if line == "":
            break
    return buf

# if __name__ == "__main__":
def handle(req):
    load_start = 0
    load_end = 0
    files = []

    # st = get_stdin()
    # bucket = st.split(' ')[0]
    # file = st.split(' ')[1].rstrip("\n")
    req = ast.literal_eval(req)
    bucket = req["bucketName"]
    file = req["fileName"]
    original_filename = file.split("-")[0]

    load_start = time.time()
    new_file = load_from_minio(bucket, file)
    load_end = time.time()

    compute_start = time.time()
    face_fun = Face()
    outdir = face_fun.handler_small(new_file, original_filename)
    compute_end = time.time()

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        outputMode = os.getenv("OUTPUTMODE")
        if outputMode == 'obj':
            bucket = os.getenv("OUTPUTBUCKET")
            store_start = time.time()
            store_to_minio(bucket, outdir)
            store_end = time.time()
    os.remove(new_file)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    response = {"bucketName" : os.getenv("OUTPUTBUCKET"), "fileName" : files[0]}
    return response