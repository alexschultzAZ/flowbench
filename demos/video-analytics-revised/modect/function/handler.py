import base64
import os
import sys
import time
import shutil
import ast
from minio import Minio
import json
from prometheus_client import Gauge,CollectorRegistry,push_to_gateway
from minio.error import InvalidResponseError
from datetime import datetime
from .handle import solve

MINIO_ADDRESS = os.getenv("ENDPOINTINPUT")
minio_client = Minio(
    MINIO_ADDRESS,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def store_to_minio(bucket, ret):
    files = os.listdir(ret)
    if len(files) == 0:
        return
    try:
        os.chdir(ret)
        for file in files:
            minio_client.fput_object(bucket, file, file)
        return
    except InvalidResponseError as err:
        print(err)


def load_from_minio(bucket, file):
    try:
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
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
def handle(req):
    request_start_ts = str(round(time.time() * 1000000000))
    compute_start = 0
    compute_end = 0
    store_start = 0
    store_end = 0
    load_start = 0
    load_end = 0

    files = []
    bucket = ''
    file = ''
    outdir = ''

    inputMode = os.getenv('INPUTMODE')
    outputBucket = os.getenv("OUTPUTBUCKET")
    mount_path = os.getenv("MOUNT_PATH")
    outputMode = os.getenv("OUTPUTMODE")
    storageMode = os.getenv("STORAGE_TYPE")
    pushGateway = os.getenv("PUSHGATEWAY_IP")
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    registry = CollectorRegistry()
    funcName = "modect"
    download_time_gauge = Gauge(f'minio_read_time_seconds_{funcName}', 'Time spent reading from Minio', registry=registry)
    upload_time_gauge = Gauge(f'minio_write_time_seconds_{funcName}', 'Time spent writing to Minio', registry=registry)
    computation_time_gauge = Gauge(f'computation_time_seconds_{funcName}', 'Time spent writing to Minio', registry=registry)
    if storageMode == 'http':
        file = os.getenv("Http_Referer")
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        f = open(new_file, "wb+")
        f.write(sys.stdin.buffer.read())
        f.close()

        original_filename = file.split("-")[0]
        compute_start = time.time()
        outdir = solve(new_file)
        compute_end = time.time()
    else:
        # st = get_stdin()
        # bucket = st.split(' ')[0]
        # file = st.split(' ')[1].rstrip("\n")
        if mn_fs:
            reqJSON = ast.literal_eval(req)
            # print(type(reqJSON))
            decodedFile = base64.b64decode(reqJSON["body"])
            file = reqJSON["headers"]["Content-Disposition"].split(";")[1].split("=")[1]
            new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
            with open(new_file,"wb") as zipfile:
                zipfile.write(decodedFile)
            outdir = solve(new_file)
        else:
            reqJSON = ast.literal_eval(req)
        #req = dict(item.split("=") for item in req.split("&"))
            bucket = reqJSON["bucketName"]
            file =  reqJSON["fileName"]
            if storageMode == 'obj':
                load_start = time.time()
                new_file = load_from_minio(bucket, file)
                load_end = time.time()
                download_time_gauge.set(load_end - load_start)
                original_filename = file.split("-")[0]
                compute_start = time.time()
                outdir = solve(new_file)
                compute_end = time.time()
                computation_time_gauge.set(compute_end - compute_start)
            else:
                response_msg, isPresent = load_from_local_storage(mount_path, bucket, file)
                if isPresent:
                    new_file = response_msg
                    outdir = solve(response_msg)
                else:
                    print('No input file to read')
                    print(response_msg)
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
            upload_start = time.time()
            store_to_minio(outputBucket, outdir)
            upload_end = time.time()
            upload_time_gauge.set(upload_end - upload_start)
        else:
            store_to_local_storage(mount_path,outputBucket,outdir)

    os.remove(new_file)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    push_to_gateway(pushGateway, job=funcName, registry=registry)
    response = {"bucketName" : outputBucket, "fileName" : files[0]}
    return response
