

# Copyright (c) Alex Ellis 2017. All rights reserved.
# Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import os
import sys
import time
import shutil
import ast
from minio import Minio
import json
from minio.error import InvalidResponseError
from datetime import datetime
from .handle import solve

MINIO_ADDRESS = "10.107.30.115:9000"
minio_client = Minio(
    MINIO_ADDRESS,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def store_to_minio(bucket, ret):
    files = os.listdir(ret)
    if len(files) == 0:
        return
    try:
        os.chdir(ret)
        for file in files:
            minio_client.fput_object(bucket, file, file)
        return
    except InvalidResponseError as err:
        print(err)


def load_from_minio(bucket, file):
    try:
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        minio_client.fget_object(bucket, file, new_file)
        return new_file
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

def handle(req):
    request_start_ts = str(round(time.time() * 1000000000))
    compute_start = 0
    compute_end = 0
    store_start = 0
    store_end = 0
    load_start = 0
    load_end = 0

    files = []
    bucket = ''
    file = ''
    outdir = ''

    inputMode = os.getenv('INPUTMODE')
    if inputMode == 'http':
        file = os.getenv("Http_Referer")
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        f = open(new_file, "wb+")
        f.write(sys.stdin.buffer.read())
        f.close()

        original_filename = file.split("-")[0]
        compute_start = time.time()
        outdir = solve(new_file)
        compute_end = time.time()
    else:
        # st = get_stdin()
        # bucket = st.split(' ')[0]
        # file = st.split(' ')[1].rstrip("\n")
        reqJSON = ast.literal_eval(req)
        #req = dict(item.split("=") for item in req.split("&"))
        bucket = reqJSON["bucketName"]
        file =  reqJSON["fileName"]
        load_start = time.time()
        new_file = load_from_minio(bucket, file)
        load_end = time.time()

        original_filename = file.split("-")[0]
        compute_start = time.time()
        outdir = solve(new_file)
        compute_end = time.time()

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        outputMode = 'obj'
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
