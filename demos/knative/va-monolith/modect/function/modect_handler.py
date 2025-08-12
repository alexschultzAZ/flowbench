import os
import sys
import time
import shutil
import ast

from .handle import solve

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
    if not os.path.exists(os.path.join(mount_path, input_dir)):
        return f"Directory '{input_dir}' does not exist.", False
    
    if not os.path.isdir(os.path.join(mount_path, input_dir)):
        return f"'{input_dir}' is not a directory.", False
    
    file_path = os.path.join(mount_path, input_dir, filename)
    
    if not os.path.isfile(file_path):
        return f"File '{filename}' does not exist in the directory '{os.path.join(mount_path, input_dir)}'.", False
    
    return file_path,True


def string_to_bool(value):
    try:
        return ast.literal_eval(value.capitalize())
    except (ValueError, SyntaxError):
        return False
    

def handle(req):
    start_time = time.time()
    files = []
    bucket = os.getenv("OUTPUTBUCKET1")
    outputBucket = os.getenv("OUTPUTBUCKET2")
    file = ''
    outdir = ''
    file =  req["fileName"]
    new_file, isPresent = load_from_local_storage("/tmp/", bucket, file)
    files_to_save, outdir = solve(new_file)



    if outdir != None and outdir != '':
        store_to_local_storage("/tmp/", outputBucket, outdir)
        
    response = {"bucketName" : outputBucket, "fileName" : files_to_save, "start_time": start_time}
    return response
