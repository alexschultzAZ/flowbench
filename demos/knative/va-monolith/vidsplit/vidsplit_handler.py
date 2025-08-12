import base64
import os
import sys
import time
import shutil
from minio import Minio
from minio.error import InvalidResponseError
from datetime import datetime
from zipfile import ZipFile
from zipfile import ZIP_STORED
import subprocess
import ast
import math
import logging

logging.basicConfig(level=logging.INFO)

MINIO_ADDRESS = os.getenv("ENDPOINTINPUT")
minio_client = Minio(
    MINIO_ADDRESS,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)


def list_files(directory, extension):
    return (f for f in os.listdir(directory) if f.endswith('.' + extension))


def load_from_bucket():
    pass


def solve(req, original_filename):
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stage = "1"

    ext = "jpg"
    quality = "1"
    os.chdir("/app/vidsplit/tmp")
    print(str(os.getcwd()))
    split_cmd = './ffmpeg -i ' + req + ' -q:v ' + quality + \
                    ' -qmin 1 -qmax 1 ' + output_dir + '/' + \
                    original_filename+'-stage-' + str(stage) + '-' + os.uname()[1] + '-' + \
                    datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + \
                    '-%04d.' + ext + '> /dev/null 2>&1'
    subprocess.check_call(split_cmd, shell=True)

    fps_cmd = './ffmpeg -i ' + req + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    fps = math.ceil(float(fps))

    gid = 1
    fid = 0
    pics = sorted(os.listdir(output_dir))
    prefix = output_dir + "/"+ original_filename +'-stage-' + stage + '-' + \
                    datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")

    gname = prefix + '.zip'
    with ZipFile(gname, 'w', ZIP_STORED) as zipObj2:
        added = 0
        while added < fps and fid < len(pics):
            path = output_dir + '/' + pics[fid]
            zipObj2.write(path, os.path.basename(path))
            added += 1
            fid += 1
    for pic in pics:
        os.remove(output_dir + '/' + pic)

    if len(os.listdir(output_dir)) == 0:
        os.rmdir(output_dir)
        return ""

    return output_dir

def store_to_minio(bucket, ret):
    files = os.listdir(ret)
    if len(files) == 0:
        return
    try:
        for file in files:
            abs_path = os.path.join(ret, file)
            if not os.path.exists(abs_path):
                print(f"File has been removed or is not available: {abs_path}")
                continue  # Skip the missing file
            minio_client.fput_object(bucket, file, abs_path)
    except InvalidResponseError as err:
        print(err)

def load_from_minio(bucket, file):
    try:
        new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
        minio_client.fget_object(bucket, file, new_file)
        return new_file
    except InvalidResponseError as err:
        logging.info("error: " + str(err))
        return err

def get_stdin():
    buf = ""
    while True:
        line = sys.stdin.readline()
        buf += line
        #print(line)
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
    
    return file_path, True


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
    

def handle(req):
    start_time = time.time()
    bucket = ''
    file = ''
    outdir = ''
    outputBucket = os.getenv("OUTPUTBUCKET1")
    response = {}
    files = []

    try:
        bucket = req["bucketName"]
        file = req["fileName"]
        
        new_file = load_from_minio(bucket, file)
        outdir = solve(new_file, file.split(".")[0])

        if outdir:
            files = os.listdir(outdir)
            store_to_local_storage("/tmp/", outputBucket, outdir) # store to local, not minio
    except Exception as e:
        logging.error(f'Exception : {str(e)}')
        response = {f"Exception: {str(e)}"}
        
    response = {"bucketName" : outputBucket, "fileName" : files[0], "pipeline_start_time": start_time, "outdir": outdir}
    return response