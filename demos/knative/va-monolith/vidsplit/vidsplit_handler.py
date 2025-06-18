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

import requests

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

# def load_from_minio(bucket, file, output_dir):
#     minioClient = Minio(os.environ["ENDPOINTINPUT"],
#                         os.environ["ACCESSKEYINPUT"],
#                         os.environ["SECRETKEYINPUT"],
#                         secure=False)
#     try:
#         minioClient.fget_object(bucket, file, output_dir + '/' + file)
#         return output_dir + '/' + file
#     except:
#         print("failed to download %s" % file)

# ffmpeg -i stage-1-input.mp4 -q:v 1 -qmin 1 -qmax 1 tst/output_%01d.jpg
def solve(req, original_filename):
    #print("stage 1 vidsplit...")
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    logging.info("output_dir is " + str(output_dir))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stage = "1"
    mode = "PIC"

    ext = "jpg"
    quality = "1"
    print(str(os.getcwd()))
    print("changing")
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
    print(f"num of pics sampled in the output directory = {len(os.listdir(output_dir))}")
    prefix = output_dir + "/"+ original_filename +'-stage-' + stage + '-' + \
                    datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    # while fid < len(pics):
    #    gname = prefix +'.zip'
    #    gid += 1
    #    with ZipFile(gname, 'w', ZIP_STORED) as zipObj2:
    #        added = 0
    #        while added < fps and fid < len(pics):
    #            path = output_dir + '/' + pics[fid]
    #            zipObj2.write(path, os.path.basename(path))
    #            added += 1
    #            fid += 1

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
            logging.info("abs path is: " + abs_path)
            minio_client.fput_object(bucket, file, abs_path)
    except InvalidResponseError as err:
        print(err)

def load_from_minio(bucket, file):
    try:
        logging.info("loading from minio")
        new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
        minio_client.fget_object(bucket, file, new_file)
        logging.info("got it")
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
            logging.info("moved to " + str(os.path.join(destination_dir, file_name)))
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
    logging.info("req is: " + str(req))
    start_time = time.time()
    bucket = ''
    file = ''
    outdir = ''
    storage_mode = os.getenv('STORAGE_TYPE')
    mount_path = os.getenv('MOUNT_PATH')
    outputBucket = os.getenv("OUTPUTBUCKET1")
    next_url = os.getenv("NEXT_URL")
    mn_fs = os.getenv("MN_FS")
    mn_fs = string_to_bool(mn_fs)
    response = {}
    funcName = "vidsplit"
    files = []

    try:
        logging.info("hello8")
        logging.info("storage mode is " + str(storage_mode))
        logging.info(str(type(storage_mode)))
        # if storage_mode == 'http':
        #     print("in http")
        #     file = os.getenv("Http_Referer")
        #     new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
        #     with open(new_file, "wb+") as f:
        #         f.write(sys.stdin.buffer.read())

        #     outdir = solve(new_file, file.split(".")[0])
        # else:
            # print("Enter")
            # st = get_stdin()
            # bucket, file = st.split(' ')
            # file = file.rstrip("\n")
            # print(file)
            #print(req)
            #req = dict(item.split("=") for item in req.split("&"))
        logging.info("req is:")
        logging.info(str(req))
        bucket = req["bucketName"]
        file = req["fileName"]
        
        # if storage_mode == 'local':
        #     logging.info("in loca")
        #     logging.info("mount_path is " + str(mount_path))
        #     response_msg, isPresent = load_from_local_storage(mount_path, bucket, file)
        #     if isPresent:
        #         logging.info("is present")
        #         new_file = response_msg
        #         outdir = solve(new_file, file.split(".")[0])
        #     else:
        #         logging.info('No input file to read')
        #         logging.info(response_msg)
        #         exit(1)
        # else: 
        #     print("loading then solving minio")
        #     load_start = time.time()
        #     new_file = load_from_minio(bucket, file)
        #     load_end = time.time()
        #     compute_start = time.time()
        #     outdir = solve(new_file, file.split(".")[0])
        #     compute_end = time.time()

        print("loading then solving minio")
        load_start = time.time()
        new_file = load_from_minio(bucket, file)
        load_end = time.time()
        compute_start = time.time()
        outdir = solve(new_file, file.split(".")[0])
        compute_end = time.time()

        if outdir:
            files = os.listdir(outdir)
            store_to_local_storage("/tmp/", outputBucket, outdir) # store to local, not minio
            # # if mn_fs:
            # #     zip_file_path = os.path.join(outdir, files[0])
            # #     with open(zip_file_path, 'rb') as zip_file:
            # #         zip_content = zip_file.read()
                
            # #     zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            # #     fileBody = {
            # #         "body": zip_base64,
            # #         "headers": {
            # #             "Content-Type": "application/zip",
            # #             "Content-Disposition": f"attachment; filename={files[0]}",
            # #             "Content-Transfer-Encoding": "base64"
            # #         },
            # #         "pipeline_start_time": start_time
            # #     }
            # #     logging.info('sending request to modect')
            # #     result = requests.post(next_url, json = fileBody)
            # #     logging.info(f"Received result from next_func: {result.text}")
            # #     end_time = time.time()
            # #     total_time = end_time - start_time
            # #     total_time_gauge.set(total_time)
            # #     push_to_gateway(pushGateway, job=funcName, registry=registry)
            # #     if result.status_code == 200:
            # #         return {"result": result.text, "total_time": total_time}
            # #     return {"message": "something went wrong"}
            # if storage_mode == 'obj':
            #     store_start = time.time()
            #     store_to_minio(outputBucket, outdir)
            #     store_end = time.time()
            #     os.remove(new_file)
            #     if os.path.exists(outdir):
            #         shutil.rmtree(outdir)
            # else:
            #     store_to_local_storage(mount_path, outputBucket, outdir)

        
        
    except Exception as e:
        logging.error(f'Exception : {str(e)}')
        response = {f"Exception: {str(e)}"}
    # push_to_gateway(pushGateway, job=funcName, registry=registry)
    # test comment
    response = {"bucketName" : outputBucket, "fileName" : files[0], "pipeline_start_time": start_time, "outdir": outdir}
    logging.info("done with vidsplit")
    return response