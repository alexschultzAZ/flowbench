# Copyright (c) Alex Ellis 2017. All rights reserved.
# Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import base64
import os
import sys
import time
import shutil
from flask import jsonify
from minio import Minio
from minio.error import InvalidResponseError
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
face_fun = Face()

def load_from_minio(bucket, file):
    try:
        new_file = "/tmp/" + file
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

def store_to_minio(mount_path, dir_name, source_dir,all):
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
            # dst_file = os.path.join(destination_dir, file_name)
            # shutil.move(src_file, dst_file)
            minio_client.fput_object("stage4", file_name, os.path.join(source_dir, file_name))
            
    except PermissionError as e:
        print(f"PermissionError: {e}")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except Exception as e:
        print(f"Error: {e}")


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
    
    print("req is " + str(req))
    start_time = time.time()
    load_start = 0
    load_end = 0
    _files = []
    all = []
    # st = get_stdin()
    # req = ast.literal_eval(req)
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    funcName = "facerec"
    outputBucket = "stage4"
       
    bucket = req['bucketName']
    _files = req["fileName"]
    # pipeline_start_time = req["pipeline_start_time"]
    for file in _files:
        original_filename = file.split("-")[0]
        
        mountPath = "/tmp/"
        response, isPresent = load_from_local_storage(mountPath,bucket,file)
        if isPresent:
            new_file = response
        else:
            print('No input file to read')
            print(response)
            exit(1)
        # face_fun = Face()
        outdir, name = face_fun.handler_small(new_file, original_filename)

        if outdir != None and outdir != '':
            files = os.listdir(outdir)
            store_to_minio(mountPath,outputBucket,outdir,all)
        
    
    # test comment
    logging.info("facerec time was " + str(time.time() - start_time))
    response = {"bucketName" : outputBucket, "fileName" : all}
    return response
