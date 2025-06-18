import base64
import os
import sys
import time
import shutil
import ast
from flask import jsonify
import json
from datetime import datetime

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
    logging.info("mount path: " + str(mount_path))
    logging.info("dir_name: " + str(dir_name))
    logging.info("source_dir: " +  str(source_dir))
    try:
        files = os.listdir(source_dir)
        logging.info("files: " + str(files))
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
            logging.info("moved " + str(os.path.join(source_dir, file_name)) + " to " + str(os.path.join(destination_dir, file_name)))
    except PermissionError as e:
        print(f"PermissionError: {e}")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except Exception as e:
        print(f"Error: {e}")


def load_from_local_storage(mount_path, input_dir, filename):
    logging.info("mount_path: " + str(mount_path))
    logging.info("input_dir: " + str(input_dir))
    logging.info("filename: " + str(filename))

    if not os.path.exists(os.path.join(mount_path, input_dir)):
        return f"Directory '{input_dir}' does not exist.", False
    
    if not os.path.isdir(os.path.join(mount_path, input_dir)):
        return f"'{input_dir}' is not a directory.", False
    
    file_path = os.path.join(mount_path, input_dir, filename)
    
    if not os.path.isfile(file_path):
        return f"File '{filename}' does not exist in the directory '{os.path.join(mount_path, input_dir)}'.", False
    
    logging.info("loaded file")
    return file_path,True


def string_to_bool(value):
    try:
        return ast.literal_eval(value.capitalize())
    except (ValueError, SyntaxError):
        return False
    

def handle(req):
    logging.info("modect2")
    logging.info(str(req))
    start_time = time.time()
    files = []
    # bucket = req['outdir']
    bucket = os.getenv("OUTPUTBUCKET1")
    outputBucket = os.getenv("OUTPUTBUCKET2")
    logging.info("bucket is: " + bucket)
    logging.info("output bucket is " + str(outputBucket))
    file = ''
    outdir = ''
    file =  req["fileName"]
    pipeline_start_time = req["pipeline_start_time"]
    file_path, isPresent = load_from_local_storage("/tmp/", bucket, file)
    logging.info("filepath of .zip " + str(file_path))
    if isPresent:
        new_file = file_path
        outdir = solve(file_path)
    else:
        logging.info('No input file to read')
        logging.info(file_path)
        exit(1)

    logging.info("done solving")

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        store_to_local_storage("/tmp/", outputBucket, outdir)
        logging.info("stored to local")

    logging.info(f'modect files length is {len(files)}')
    response = {"bucketName" : outputBucket, "fileName" : files, "start_time": start_time}
    return response
