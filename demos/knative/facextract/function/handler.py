import base64
import os
import sys
import time
import shutil
from minio import Minio
from minio.error import InvalidResponseError
from prometheus_client import Gauge,CollectorRegistry,push_to_gateway
from datetime import datetime
from .handler1 import *
import ast

MINIO_ADDRESS = os.getenv("ENDPOINTINPUT")
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

def store_to_minio(bucket, ret,all):
    files = os.listdir(ret)
    if len(files) == 0:
        return

    # Put an object.
    try:
        os.chdir(ret)
        for file in files:
            minio_client.fput_object(bucket, file, file)
            all.append(file)
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

    input_dir = os.path.join(mount_path, input_dir)
    if not os.path.exists(input_dir):
        return f"Directory '{input_dir}' does not exist.", False
    
    if not os.path.isdir(input_dir):
        return f"'{input_dir}' is not a directory.", False
    
    file_path = os.path.join(mount_path, input_dir, filename)
    
    if not os.path.isfile(file_path):
        return f"File '{filename}' does not exist in the directory '{input_dir}'.", False
    return file_path,True
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

def string_to_bool(value):
    try:
        return ast.literal_eval(value.capitalize())
    except (ValueError, SyntaxError):
        return False
# if __name__ == "__main__":
def handle(req):
    files = []
    inputMode = os.getenv("INPUTMODE")
    outputMode = os.getenv("OUTPUTMODE")
    outputBucket = os.getenv("OUTPUTBUCKET")
    storageMode = os.getenv("STORAGE_TYPE")
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    pushGateway = os.getenv("PUSHGATEWAY_IP")
    registry = CollectorRegistry()
    funcName = "facextract"
    all = []
    download_time_gauge = Gauge(f'minio_read_time_seconds_{funcName}', 'Time spent reading from Minio', registry=registry)
    upload_time_gauge = Gauge(f'minio_write_time_seconds_{funcName}', 'Time spent writing to Minio', registry=registry)
    computation_time_gauge = Gauge(f'computation_time_seconds_{funcName}', 'Time spent writing to Minio', registry=registry)
    #req = ast.literal_eval(req)
    if mn_fs:
        image_data = base64.b64decode(req["body"])
        file = req["headers"]["Content-Disposition"].split(";")[1].split("=")[1]
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        with open(new_file,"wb") as image_file:
            image_file.write(image_data)
        original_filename = file.split("-")[0]
    else:
        bucket = req["bucketName"]
        _files = req["fileName"]
        for file in _files:
            original_filename = file.split("-")[0]
            if storageMode == 'obj':
                load_start = time.time()
                new_file = load_from_minio(bucket, file)
                load_end = time.time()
                download_time_gauge.set(load_end - load_start)
            else:
                mountPath = os.getenv("MOUNT_PATH")
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
            computation_time_gauge.set(compute_end - compute_start)

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
                    store_to_minio(outputBucket, outdir,all)
                    upload_end = time.time()
                    upload_time_gauge.set(upload_end - upload_start)
                else:
                    store_to_local_storage(mountPath,outputBucket,outdir)
                os.remove(new_file)
                if os.path.exists(outdir):
                    shutil.rmtree(outdir)
                push_to_gateway(pushGateway, job=funcName, registry=registry)
    response = {"bucketName" : outputBucket, "fileName" : all}
    return response