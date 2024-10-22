# Copyright (c) Alex Ellis 2017. All rights reserved.
# Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import base64
import os
import sys
import time
import shutil
import requests
from minio import Minio
from minio.error import InvalidResponseError
from prometheus_client import Gauge,CollectorRegistry,push_to_gateway
from .handler1 import *
from datetime import datetime
import ast

import logging

logging.basicConfig(level=logging.INFO)

MINIO_ADDRESS = os.environ["ENDPOINTINPUT"]
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
        logging.info(err)

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
        logging.info(err)

def get_stdin():
    buf = ""
    while(True):
        line = sys.stdin.readline()
        buf += line
        if line == "":
            break
    return buf

def store_to_minio(bucket, ret,all):
    files = os.listdir(ret)
    if len(files) == 0:
        return

    # Put an object.
    try:
        os.chdir(ret)
        for file in files:
            minio_client.fput_object(bucket, file, file)
            all.append(file)
        return
    except InvalidResponseError as err:
        logging.info(err)

def store_to_local_storage(mount_path, dir_name, source_dir,all):
    try:
        files = os.listdir(source_dir)
        if len(files) == 0:
            return
        if not os.path.exists(mount_path):
            os.makedirs(mount_path)
               
        destination_dir = os.path.join(mount_path, os.path.basename(dir_name))
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
       
        for file_name in files:
            all.append(file_name)
            src_file = os.path.join(source_dir, file_name)
            dst_file = os.path.join(destination_dir, file_name)
            shutil.move(src_file, dst_file)
    except PermissionError as e:
        logging.info(f"PermissionError: {e}")
    except FileNotFoundError as e:
        logging.info(f"FileNotFoundError: {e}")
    except Exception as e:
        logging.info(f"Error: {e}")


def load_from_local_storage(mount_path, input_dir, filename):

    input_dir = os.path.join(mount_path, input_dir)
    if not os.path.exists(input_dir):
        return f"Directory '{input_dir}' does not exist.", False
   
    if not os.path.isdir(input_dir):
        return f"'{input_dir}' is not a directory.", False
   
    file_path = os.path.join(mount_path, input_dir, filename)
   
    if not os.path.isfile(file_path):
        return f"File '{filename}' does not exist in the directory '{input_dir}'.", False
    return file_path,True
def string_to_bool(value):
    try:
        return ast.literal_eval(value.capitalize())
    except (ValueError, SyntaxError):
        return False
# if __name__ == "__main__":
def handle(req):
    function_start_time = time.time()
    load_start = 0
    load_end = 0
    _files = []
    all = []
    # st = get_stdin()
    # req = ast.literal_eval(req)
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    pushGateway = os.getenv("PUSHGATEWAY_IP")
    registry = CollectorRegistry()
    funcName = "facerec"
    outputBucket = os.getenv("OUTPUTBUCKET")
    download_time_gauge = Gauge(f'minio_read_time_seconds_{funcName}', 'Time spent reading from Minio', registry=registry)
    upload_time_gauge = Gauge(f'minio_write_time_seconds_{funcName}', 'Time spent writing to Minio', registry=registry)
    computation_time_gauge = Gauge(f'computation_time_seconds_{funcName}', 'Time spent writing to Minio', registry=registry)
    total_time_gauge = Gauge(f'time_taken_{funcName}', f'Time took to process this {funcName}', registry=registry)

    pipeline_total_time_gauge = Gauge(f'pipeline_time_taken', f'Time took to process the entire pipeline', registry=registry)

    if mn_fs:
        image_data = base64.b64decode(req["body"])
        file = req["headers"]["Content-Disposition"].split(";")[1].split("=")[1]
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        with open(new_file,"wb") as image_file:
            image_file.write(image_data)
        original_filename = file.split("-")[0]
    else:
       
        inputMode = os.getenv("INPUTMODE")
        outputMode = os.getenv("OUTPUTMODE")
        storageMode = os.getenv("STORAGE_TYPE")
        bucket = req['bucketName']
        _files = req["fileName"]
        pipeline_start_time = req["pipeline_start_time"]
        for file in _files:
            original_filename = file.split("-")[0]
            if storageMode == 'obj':
                load_start = time.time()
                new_file = load_from_minio(bucket, file)
                load_end = time.time()
                download_time_gauge.set(load_end - load_start)
            else:
                mountPath = os.getenv("MOUNT_PATH")
                response, isPresent = load_from_local_storage(mountPath,bucket,file)
                if isPresent:
                    new_file = response
                else:
                    logging.info('No input file to read')
                    logging.info(response)
                    exit(1)
            compute_start = time.time()
            face_fun = Face()
            outdir, name = face_fun.handler_small(new_file, original_filename)
            compute_end = time.time()
            computation_time_gauge.set(compute_end - compute_start)

            if outdir != None and outdir != '':
                files = os.listdir(outdir)
                if mn_fs:
                    file_path = os.path.join(outdir,files[0])
                    new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
                    file_content = ''
                    with open(file_path, "r") as text_file:
                        file_content = text_file.read()
                    with open(new_file,"w") as dest_file:
                        dest_file.write(file_content)
                    return {
                        "statusCode": 200,
                        "body": f"Written to file {files[0]}",
                        "headers": {
                            "Content-Type": "image/text",
                            "Content-Disposition": f"attachment; filename={files[0]}",
                            "Content-Transfer-Encoding": "base64"
                        }
                    }
                if storageMode == 'obj':
                    upload_start = time.time()
                    store_to_minio(outputBucket, outdir,all)
                    upload_end = time.time()
                    upload_time_gauge.set(upload_end - upload_start)
                    #os.remove(new_file)
                    if os.path.exists(outdir):
                        shutil.rmtree(outdir)
                else:
                    store_to_local_storage(mountPath,outputBucket,outdir,all)
    total_time_gauge.set(time.time() - function_start_time)
    pipeline_total_time_gauge.set(time.time() - pipeline_start_time)
    push_to_gateway(pushGateway, job=funcName, registry=registry)
    response = {"bucketName" : outputBucket, "fileName" : all, "pipeline_start_time": pipeline_start_time, "total_time": time.time()-(pipeline_start_time if pipeline_start_time else time.time())}
    return response 