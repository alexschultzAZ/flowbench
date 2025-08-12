import os
import sys
import time
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
        print(err)

def get_stdin():
    buf = ""
    while(True):
        line = sys.stdin.readline()
        buf += line
        if line == "":
            break
    return buf

def store_to_minio(bucket, file):
    try:
        minio_client.fput_object(bucket, os.path.basename(file), file)
        return
    except InvalidResponseError as err:
        logging.info(err)


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
    start_time = time.time()
    _files = []
    all = []
    outputBucket = os.getenv("OUTPUTBUCKET4")
       
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
        file_to_save = face_fun.handler_small(new_file, original_filename)

        store_to_minio(outputBucket, file_to_save)
        all.append(file_to_save)
        
    
    # test comment
    logging.info("facerec time was " + str(time.time() - start_time))
    response = {"bucketName" : outputBucket, "fileName" : all}
    return response
