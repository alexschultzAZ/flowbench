from minio import Minio
from datetime import datetime
from zipfile import ZipFile
from zipfile import ZIP_STORED
import subprocess
import math
import os

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
    print("stage 1 vidsplit...")
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stage = "1"
    mode = "PIC"

    ext = "jpg"
    quality = "1"
    split_cmd = 'ffmpeg -i ' + req + ' -q:v ' + quality + \
                    ' -qmin 1 -qmax 1 ' + output_dir + '/' + \
                    original_filename+'-stage-' + str(stage) + '-' + os.uname()[1] + '-' + \
                    datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + \
                    '-%04d.' + ext
    subprocess.check_call(split_cmd, shell=True)

    fps_cmd = 'ffmpeg -i ' + req + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    fps = math.ceil(float(fps))

    gid = 1
    fid = 0
    pics = sorted(os.listdir(output_dir))
    print(f"num of pics sampled in the output directory = {len(os.listdir(output_dir))}")
    prefix = output_dir + "/"+ original_filename +'-stage-' + stage
    while fid < len(pics):
       gname = prefix +'.zip'
       gid += 1
       with ZipFile(gname, 'w', ZIP_STORED) as zipObj2:
           added = 0
           while added < fps and fid < len(pics):
               path = output_dir + '/' + pics[fid]
               zipObj2.write(path, os.path.basename(path))
               added += 1
               fid += 1

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
