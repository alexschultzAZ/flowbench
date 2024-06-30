import os
import sys
import time
import shutil
from minio import Minio
from minio.error import InvalidResponseError
from datetime import datetime
from .facextract_handler1 import *
import ast

MINIO_ENDPOINT = os.getenv('ENDPOINTINPUT')
minio_client = Minio(
    MINIO_ENDPOINT,
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

def load_from_local_storage(mount_path, input_dir, filename):
    # Check if the input directory exists
    input_dir = os.path.join(mount_path, input_dir)
    if not os.path.exists(input_dir):
        return f"Directory '{input_dir}' does not exist.", False
    
    # Check if the input directory is indeed a directory
    if not os.path.isdir(input_dir):
        return f"'{input_dir}' is not a directory.", False
    
    # Construct the full file path
    file_path = os.path.join(mount_path, input_dir, filename)
    
    # Check if the file exists at the constructed file path
    if not os.path.isfile(file_path):
        return f"File '{filename}' does not exist in the directory '{input_dir}'.", False
    
    return file_path, True

def store_to_local_storage(mount_path, dir_name, source_dir):
    files = os.listdir(source_dir)
    if len(files) == 0:
        return
    if not os.path.exists(mount_path):
        os.makedirs(mount_path)
            
    destination_dir = os.path.join(mount_path, os.path.basename(dir_name))
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    # Move files from outdir to destination_dir
    for file_name in files:
        src_file = os.path.join(source_dir, file_name)
        dst_file = os.path.join(destination_dir, file_name)
        shutil.move(src_file, dst_file)

# if __name__ == "__main__":
def facextract_handler(req):
    load_start = 0
    load_end = 0
    files = []

    # st = get_stdin()
    # bucket = st.split(' ')[0]
    # file = st.split(' ')[1].rstrip("\n")
    # req = ast.literal_eval(req)
    storage_mode = os.getenv('STORAGE_TYPE')
    mount_path = os.getenv('MOUNT_PATH')
    output_bucket_name = os.getenv('OUTPUTBUCKET3')
    outputMode = os.getenv("OUTPUTMODE")
    bucket = req["bucketName"]
    file = req["fileName"]
    original_filename = file.split("-")[0]

    if storage_mode == 'local':
        response, isPresent = load_from_local_storage(mount_path=mount_path, input_dir=bucket, filename=file)
                
        if isPresent:
            new_file = response
        else:
            print('No input file to read')
            print(response)
            exit(1)
    else:

        load_start = time.time()
        new_file = load_from_minio(bucket, file)
        load_end = time.time()

    compute_start = time.time()
    face_fun = Face()
    outdir = face_fun.handler_small(new_file, original_filename)
    compute_end = time.time()

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        if storage_mode == 'local':
            new_dir = output_bucket_name
            store_to_local_storage(mount_path=mount_path, dir_name=new_dir, source_dir=outdir)
        
        elif storage_mode == 'obj':
            bucket = output_bucket_name
            store_start = time.time()
            store_to_minio(bucket, outdir)
            store_end = time.time()
    os.remove(new_file)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    response = {"bucketName" : output_bucket_name, "fileName" : files[0]}
    return response
