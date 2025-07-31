import base64
import os
import sys
import time
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

def store_to_minio(bucket, ret):
    files_out = []
    files = os.listdir(ret)
    if len(files) == 0:
        return
    # logging.info("ret: " + str(ret))
    os.chdir(ret)
    for file in files:
        # logging.info("flret: " + str(file))
        try:
            minio_client.fput_object(bucket, file, file)
            files_out.append(file)
        except Exception as err:
            logging.info("skipping file: " + str(file))
            logging.info(err)
    return files_out


def load_from_minio(bucket, file):
    try:
        logging.info("bucket: " + str(bucket))
        logging.info("file: " + str(file))
        new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
        logging.info("new_file: " + str(new_file))
        minio_client.fget_object(bucket, file, new_file)
        logging.info("loaded")
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

    files = []
    bucket = ''
    file = ''
    outdir = ''

    inputMode = os.getenv('INPUTMODE')
    outputBucket = os.getenv("OUTPUTBUCKET")
    mount_path = os.getenv("MOUNT_PATH")
    outputMode = os.getenv("OUTPUTMODE")
    storageMode = os.getenv("STORAGE_TYPE")
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    funcName = "modect"

    if storageMode == 'http':
        file = os.getenv("Http_Referer")
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        f = open(new_file, "wb+")
        f.write(sys.stdin.buffer.read())
        f.close()

        original_filename = file.split("-")[0]
        # compute_start = time.time()
        outdir = solve(new_file)
        # compute_end = time.time()
    else:
        # st = get_stdin()
        # bucket = st.split(' ')[0]
        # file = st.split(' ')[1].rstrip("\n")
        if mn_fs:
            # reqJSON = ast.literal_eval(req)
            # logging.info(type(reqJSON))
            decodedFile = base64.b64decode(req["body"])
            file = req["headers"]["Content-Disposition"].split(";")[1].split("=")[1]
            new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
            with open(new_file,"wb") as zipfile:
                zipfile.write(decodedFile)
            outdir = solve(new_file)
        else:
            #reqJSON = ast.literal_eval(req)
        #req = dict(item.split("=") for item in req.split("&"))
            bucket = req["bucketName"]
            file =  req["fileName"]
            pipeline_start_time = req["pipeline_start_time"]
            if storageMode == 'obj':
                # load_start = time.time()
                new_file = load_from_minio(bucket, file)
                # load_end = time.time()
                original_filename = file.split("-")[0]
                # compute_start = time.time()
                outdir = solve(new_file)
                # compute_end = time.time()
            else:
                response_msg, isPresent = load_from_local_storage(mount_path, bucket, file)
                if isPresent:
                    new_file = response_msg
                    outdir = solve(response_msg)
                else:
                    logging.info('No input file to read')
                    logging.info(response_msg)
                    exit(1)

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        if mn_fs:
            image_path = os.path.join(outdir,files[0])
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            return {
                "statusCode": 200,
                "body": image_base64,
                "headers": {
                    "Content-Type": "image/jpeg",
                    "Content-Disposition": f"attachment; filename={files[0]}",
                    "Content-Transfer-Encoding": "base64"
                }
            } 
        if storageMode == 'obj':
            # upload_start = time.time()
            logging.info("files was: " + str(len(files)))
            files = store_to_minio(outputBucket, outdir)
            logging.info("files is now: " + str(len(files)))
            # upload_end = time.time()
            os.remove(new_file)
            if os.path.exists(outdir):
                shutil.rmtree(outdir)
        else:
            store_to_local_storage(mount_path,outputBucket,outdir)

   
    logging.info(f'modect files len = {len(files)}')
    response = {"bucketName" : outputBucket, "fileName" : files, "pipeline_start_time": pipeline_start_time}
    return response
