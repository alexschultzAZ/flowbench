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
import math

MINIO_ADDRESS = "10.107.30.115:9000"
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

def load_from_minio(bucket, file, output_dir):
    minioClient = Minio(os.environ["ENDPOINTINPUT"],
                        os.environ["ACCESSKEYINPUT"],
                        os.environ["SECRETKEYINPUT"],
                        secure=False)
    try:
        minioClient.fget_object(bucket, file, output_dir + '/' + file)
        return output_dir + '/' + file
    except:
        print("failed to download %s" % file)

# ffmpeg -i stage-1-input.mp4 -q:v 1 -qmin 1 -qmax 1 tst/output_%01d.jpg
def solve(req, original_filename):
    #print("stage 1 vidsplit...")
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stage = "1"
    mode = "PIC"

    ext = "jpg"
    quality = "1"
    os.chdir("/home/app/function/tmp")
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
    #print(f"num of pics sampled in the output directory = {len(os.listdir(output_dir))}")
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
            minio_client.fput_object(bucket, file, os.path.join(ret, file))
    except InvalidResponseError as err:
        print(err)

def load_from_minio(bucket, file):
    try:
        new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
        minio_client.fget_object(bucket, file, new_file)
        return new_file
    except InvalidResponseError as err:
        print(err)

def get_stdin():
    buf = ""
    while True:
        line = sys.stdin.readline()
        buf += line
        #print(line)
        if line == "":
            break
    return buf

# if __name__ == "__main__":
def handle(req):
    bucket = ''
    file = ''
    outdir = ''
    inputMode = os.getenv("INPUTMODE")
    response = {}
    try:
        if inputMode == 'http':
            file = os.getenv("Http_Referer")
            new_file = f"/tmp/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}-{file}"
            with open(new_file, "wb+") as f:
                f.write(sys.stdin.buffer.read())

            compute_start = time.time()
            outdir = solve(new_file, file.split(".")[0])
            compute_end = time.time()
        else:
            # print("Enter")
            # st = get_stdin()
            # bucket, file = st.split(' ')
            # file = file.rstrip("\n")
            # print(file)
            #print(req)
            req = dict(item.split("=") for item in req.split("&"))
            bucket = req["bucketName"]
            file = req["fileName"]
            #print(bucket,file)
            load_start = time.time()
            new_file = load_from_minio(bucket, file)
            load_end = time.time()

            compute_start = time.time()
            outdir = solve(new_file, file.split(".")[0])
            #print(outdir)
            compute_end = time.time()

        if outdir:
            files = os.listdir(outdir)
            outputMode = os.getenv("OUTPUTMODE")
            if outputMode == 'obj':
                bucket = os.getenv("OUTPUTBUCKET")
                store_start = time.time()
                store_to_minio(bucket, outdir)
                store_end = time.time()

        os.remove(new_file)
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
    except Exception as e:
        response.update({"exception": str(e)})
    response = {"bucketName" : os.getenv("OUTPUTBUCKET"), "fileName" : files[0]}
    return response