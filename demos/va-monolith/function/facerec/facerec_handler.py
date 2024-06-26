# Copyright (c) Alex Ellis 2017. All rights reserved.
# Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import os
import sys
import time
import shutil
import requests
from minio import Minio
from minio.error import InvalidResponseError
from .facerec_handler1 import *
from datetime import datetime
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
def facerec_handler(req):
    files = []

    # st = get_stdin()
    # req = ast.literal_eval(req)
    bucket = req["bucketName"]
    file = req["fileName"]
    original_filename = file.split("-")[0]

    new_file = load_from_minio(bucket, file)

    face_fun = Face()
    outdir, name = face_fun.handler_small(new_file, original_filename)

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        outputMode = os.getenv("OUTPUTMODE")
        if outputMode == 'obj':
            bucket = os.getenv("OUTPUTBUCKET4")
            store_to_minio(bucket, outdir)

    # connect to influxdb and log latency numbers

    os.remove(new_file)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    response = {"bucketName" : os.getenv("OUTPUTBUCKET4"), "fileName" : files[0]}
    return response

