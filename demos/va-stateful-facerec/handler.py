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
from .handler1 import *
from datetime import datetime
import ast

MINIO_ADDRESS = "192.168.0.219:9000"
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
def store_to_local_storage(mount_path, dir_name, source_dir):
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
            src_file = os.path.join(source_dir, file_name)
            dst_file = os.path.join(destination_dir, file_name)
            shutil.move(src_file, dst_file)
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
    load_start = 0
    load_end = 0
    files = []

    # st = get_stdin()
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    outputBucket = os.getenv("OUTPUTBUCKET")
    inputMode = os.getenv("INPUTMODE")
    outputMode = os.getenv("OUTPUTMODE")
    storageMode = os.getenv("STORAGE_TYPE")
    req = ast.literal_eval(req)
    if mn_fs:
        image_data = base64.b64decode(req["body"])
        file = req["headers"]["Content-Disposition"].split(";")[1].split("=")[1]
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        with open(new_file,"wb") as image_file:
            image_file.write(image_data)
        original_filename = file.split("-")[0]
    else:
        bucket = req["bucketName"]
        file = req["fileName"]
        original_filename = file.split("-")[0]
        if storageMode == 'obj':
            new_file = load_from_minio(bucket, file)
        else:
            mountPath = os.getenv("MOUNT_PATH")
            response, isPresent = load_from_local_storage(mountPath,bucket,file)
            if isPresent:
                new_file = response
            else:
                print('No input file to read')
                print(response)
                exit(1)

    face_fun = Face()
    outdir, name = face_fun.handler_small(new_file, original_filename)

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
                "body": f"Written to file {files[0]}",
                "headers": {
                    "Content-Type": "image/text",
                    "Content-Disposition": f"attachment; filename={files[0]}",
                    "Content-Transfer-Encoding": "base64"
                }
            } 
        if storageMode == 'obj':
            store_to_minio(outputBucket, outdir)
        else:
            store_to_local_storage(mountPath,outputBucket,outdir)


    os.remove(new_file)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    response = {"bucketName" : outputBucket, "fileName" : files[0]}
    return response

