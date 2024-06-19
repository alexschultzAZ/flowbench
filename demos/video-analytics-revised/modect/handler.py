from datetime import datetime
from zipfile import ZipFile
from minio.error import S3Error
from minio import Minio
import imutils
import cv2
import os, shutil


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

def loadVideoesFromMinIO(bucket_name,download_dir):
    try:
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            file_path = os.path.join(download_dir, obj.object_name)
            minio_client.fget_object(bucket_name, obj.object_name, file_path)
            print(f"Downloaded {obj.object_name} to {file_path}")
    except S3Error as err:
        print(f"Failed to download videos: {err}")

def uploadToBucket(bucket_name,object_name):
    minio_client.fput_object(bucket_name, object_name)

def detect(lgray, frame, min_area):
    frame = imutils.resize(frame, width=320)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    frameDelta = cv2.absdiff(lgray, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts:
        if cv2.contourArea(c) > min_area:
            return True, gray
    return False, gray

def handle():
    print("stage 2 modect...")
    # output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)

    stage = "2"
    min_area = 1

    input_dir = createFolder("input")
    # output_dir = createFolder("output")
    loadVideoesFromMinIO("stage1",input_dir)
    # with ZipFile(req, "r") as zip_ref:
    #     zip_ref.extractall(input_dir)

    # load the reference frame
    last_gray = None

    # rename the files for logging purpose
    #pics = sorted(os.listdir(input_dir))
    # prefix_prev = "-".join(segments[:-1])
    # segments[1] = stage
    # prefix_now = "-".join(segments[:-1])
    # ext = segments[-1].split(".")[1]
    # skip = 1

    # idx = 1
    # while idx < len(pics):
    #     if skip == 1 or idx % skip == 1:
    #         segments = pics[idx].split("-")
    #         segments[1] = stage
    #         shutil.move(input_dir + "/" + pics[idx],  \
    #                 output_dir + "/" + "-".join(segments))
    #     idx += 1

    # if one frame contains motion, hand all coming frames to the next stage, otherwise remove the frame
    pics = sorted(os.listdir(input_dir))
    for pic in pics:
        path = os.path.join(input_dir, pic)
        frame = cv2.imread(path, cv2.IMREAD_COLOR)
        if frame is None:
            print("failed to open picture %s" % path)
            return ''

        if last_gray is None:
            frame = imutils.resize(frame, width=320)
            last_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_gray = cv2.GaussianBlur(last_gray, (21, 21), 0)
            continue

        detected, gray = detect(last_gray, frame, min_area)
        if detected:
            print(pic)
            uploadToBucket("stage2",pic)
            break
        else:
            last_gray = gray

    # if len(os.listdir(output_dir)) == 0:
    #     os.rmdir(output_dir)
    #     return ''

    # return output_dir

handle()