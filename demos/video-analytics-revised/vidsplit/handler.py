from datetime import datetime
from minio import Minio
from minio.error import S3Error
import os
import subprocess
import math
# ffmpeg -i stage-1-input.mp4 -q:v 1 -qmin 1 -qmax 1 tst/output_%01d.jpg
INPUT_DIR = "/tmp/"
MINIO_ADDRESS = "172.17.0.2:9000"
minio_client = Minio(
    MINIO_ADDRESS,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def createFolder(mode):
    output_dir = f"./{mode}-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def upload_file(bucket_name, directory_path):
    try:
        for root, _, files in os.walk(directory_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                minio_client.fput_object(
                    bucket_name=bucket_name,
                    object_name=file_name,
                    file_path=file_path
                )
                print(f"File '{file_name}' uploaded successfully to bucket '{bucket_name}'.")
    except S3Error as err:
        print(f"Failed to upload file: {err}")


def downloadVideo(bucket_name,object_name):
    try:
        folder_path = createFolder("input")
        updated_file_path = os.path.join(folder_path,object_name)
        minio_client.fget_object(bucket_name, object_name, updated_file_path)
        print(f"Video {object_name} downloaded successfully")
        return updated_file_path
    except S3Error as err:
        print(f"Failed to download video: {err}")

def handle():
    print("stage 1 vidsplit...")
    # output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)

    stage = "1"
    # mode = os.getenv('VIDSPLIT_MODE')
    file_path = downloadVideo("stage0","test_00.mp4")
    output_dir = createFolder("output")
    ext = "jpg"
    quality = "1"
    split_cmd = 'ffmpeg -i ' + file_path + ' -q:v ' + quality + \
                    ' -qmin 1 -qmax 1 ' + output_dir + '/' + \
                    'stage-' + str(stage) + "-" + \
                    datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + \
                    '-%04d.' + ext
    subprocess.check_call(split_cmd, shell=True)

    # fps_cmd = 'ffmpeg -i ' + file_path + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    # fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    # fps = math.ceil(float(fps))
    upload_file("stage1",output_dir)
    # gid = 1
    # fid = 0
    # pics = sorted(os.listdir(output_dir))
    # print(f"num of pics sampled in the output directory = {len(os.listdir(output_dir))}")
    # prefix = output_dir + "/"+ original_filename +'-stage-' + stage + '-' + \
    #             datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    # #while fid < len(pics):
    # #    gname = prefix + '-' + str(gid) + '.zip'
    # #    gid += 1
    # #    with ZipFile(gname, 'w', ZIP_STORED) as zipObj2:
    # #        added = 0
    # #        while added < fps and fid < len(pics):
    # #            path = output_dir + '/' + pics[fid]
    # #            zipObj2.write(path, os.path.basename(path))
    # #            added += 1
    # #            fid += 1

    # gname = prefix + '-' + str(gid) + '.zip'
    # with ZipFile(gname, 'w', ZIP_STORED) as zipObj2:
    #     added = 0
    #     while added < fps and fid < len(pics):
    #         path = output_dir + '/' + pics[fid]
    #         zipObj2.write(path, os.path.basename(path))
    #         added += 1
    #         fid += 1
    # for pic in pics:
    #     os.remove(output_dir + '/' + pic)

    # if len(os.listdir(output_dir)) == 0:
    #     os.rmdir(output_dir)
    #     return ""

    # return output_dir
handle()