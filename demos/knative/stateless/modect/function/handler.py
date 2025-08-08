import os
import sys
import shutil
import ast
from minio import Minio
from minio.error import InvalidResponseError
from datetime import datetime
from .handle import solve

import logging

logging.basicConfig(level=logging.INFO)

MINIO_ADDRESS = os.getenv("ENDPOINTINPUT")
minio_client = Minio(
    MINIO_ADDRESS,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def store_to_minio(bucket, output_dir, files_to_save):
    if len(files_to_save) == 0:
        return

    for file in files_to_save:
        try:
            minio_client.fput_object(bucket, os.path.basename(file), os.path.join(output_dir, file))
        except Exception as err:
            logging.info("skipping file: " + str(file))


def load_from_minio(bucket, file):
    try:

        new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
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
    
def handle(req):

    bucket = ''
    file = ''
    outdir = ''

    outputBucket = os.getenv("OUTPUTBUCKET")
    mount_path = os.getenv("MOUNT_PATH")
    storageMode = os.getenv("STORAGE_TYPE")
    bucket = req["bucketName"]
    file =  req["fileName"]
    pipeline_start_time = req["pipeline_start_time"]
    if storageMode == 'obj':
        new_file = load_from_minio(bucket, file)
        # outdir = solve(new_file) # need to get this to spit back the .jpg file names specificallyh not just a dir thlen feed those to store to minio
        files_to_save, output_dir = solve(new_file)
    else: # if local
        new_file, isPresent = load_from_local_storage(mount_path, bucket, file)
        files_to_save, outdir = solve(new_file)
        
    if storageMode == 'obj':
        store_to_minio(outputBucket, output_dir, files_to_save)
    else:
        store_to_local_storage(mount_path,outputBucket,outdir)

   
    # logging.info(f'modect files len = {len(files_to_save)}')
    response = {"bucketName" : outputBucket, "fileName" : files_to_save, "pipeline_start_time": pipeline_start_time}
    return response
