import base64
import os
import sys
import time
import shutil
from datetime import datetime

from .handler1 import *
import ast
import logging

logging.basicConfig(level=logging.INFO)


def get_stdin():
    buf = ""
    while(True):
        line = sys.stdin.readline()
        buf += line
        if line == "":
            break
    return buf

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


def store_to_local_storage(mount_path, dir_name, source_dir, all):
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
        print(f"PermissionError: {e}")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except Exception as e:
        print(f"Error: {e}")

def string_to_bool(value):
    try:
        return ast.literal_eval(value.capitalize())
    except (ValueError, SyntaxError):
        return False
# if __name__ == "__main__":
def handle(req):
    start_time = time.time()
    files = []
    inputMode = os.getenv("INPUTMODE")
    outputMode = os.getenv("OUTPUTMODE")
    outputBucket = "stage3"
    storageMode = os.getenv("STORAGE_TYPE")
    next_url = os.getenv('NEXT_URL')
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    logging.info(f'mn_fs value is {mn_fs}')
    funcName = "facextract"
    all = []

    bucket = req["bucketName"]
    _files = req["fileName"]
    # pipeline_start_time = req["pipeline_start_time"]
    for file in _files:
        original_filename = file.split("-")[0]
        
        mountPath = "/tmp/"
        response_msg, isPresent = load_from_local_storage(mountPath, bucket, file)
        if isPresent:
            new_file = response_msg
        else:
            print('No input file to read')
            print(response_msg)
            exit(1)
        compute_start = time.time()
        face_fun = Face()
        outdir = face_fun.handler_small(new_file, original_filename)
        compute_end = time.time()
        # computation_time_gauge.set(compute_end - compute_start)
        new_outdir = os.path.join("tmp", "stage3", os.path.basename(outdir))
        if outdir != None and outdir != '':
            store_to_local_storage(mountPath,outputBucket,outdir,all)
        
        
    # push_to_gateway(pushGateway, job=funcName, registry=registry)
    # test comment
    logging.info("faceextract time was " + str(time.time() - start_time))
    response = {"bucketName" : outputBucket, "fileName" : all, "start_time": start_time}
    return response