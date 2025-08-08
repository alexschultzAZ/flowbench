# Copyright (c) Alex Ellis 2017. All rights reserved.
# Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import os
import sys
import time
import shutil
from minio import Minio
from minio.error import InvalidResponseError
from .handler1 import *
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

face_fun = Face()

def load_from_minio(bucket, file):
    try:
        new_file = "/tmp/" + file
        minio_client.fget_object(bucket, file, new_file)
        return new_file
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

def store_to_minio(bucket, file):
    # Put an object.
    try:
        minio_client.fput_object(bucket, os.path.basename(file), file)
        return
    except InvalidResponseError as err:
        logging.info(err)

def store_to_local_storage(mount_path, dir_name, file_to_save):
    if not os.path.exists(mount_path):
        os.makedirs(mount_path)
            
    destination_dir = os.path.join(mount_path, os.path.basename(dir_name))
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    dst_file = os.path.join(destination_dir, os.path.basename(file_to_save))
    shutil.move(file_to_save, dst_file)


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
    
    
def handle(req):
    _files = []
    all = []
    outputBucket = os.getenv("OUTPUTBUCKET")
    storageMode = os.getenv("STORAGE_TYPE")
    bucket = req['bucketName']
    _files = req["fileName"]
    pipeline_start_time = req["pipeline_start_time"]
    
    for index, file in enumerate(_files):
        original_filename = file.split("-")[0]
        if storageMode == 'obj':
            new_file = load_from_minio(bucket, file)
        else:
            mountPath = os.getenv("MOUNT_PATH")
            response, isPresent = load_from_local_storage(mountPath,bucket,file)
            if isPresent:
                new_file = response
            else:
                logging.info('No input file to read')
                logging.info(response)
                exit(1)
        
        # compute_start = time.time()
        file_to_save = face_fun.handler_small(new_file, original_filename)
        # compute_stop = time.time()
        # logging.info("compute time: " + str(compute_stop - compute_start))
        if storageMode == 'obj':
            store_to_minio(outputBucket, file_to_save)
        else:
            store_to_local_storage(mountPath, outputBucket, file_to_save)
        all.append(file_to_save)
    
    response = {"bucketName" : outputBucket, "fileName" : all, "pipeline_start_time": pipeline_start_time, "total_time": time.time()-(pipeline_start_time if pipeline_start_time else time.time())}
    return response 