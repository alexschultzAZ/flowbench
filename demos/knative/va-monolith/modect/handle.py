from datetime import datetime
from zipfile import ZipFile
import imutils
import cv2
import os, shutil

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

def solve(req):
    # print("stage 2 modect...")
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stage = os.getenv('PIPELINE_STAGE')
    min_area = float(os.getenv('MODECT_MIN_AREA'))

    input_dir = req.split('.')[0]
    with ZipFile(req, "r") as zip_ref:
        zip_ref.extractall(input_dir)

    # load the reference frame
    last_gray = None

    # rename the files for logging purpose
    pics = sorted(os.listdir(input_dir))
    segments = req.split("/")[-1].split("-")
    prefix_prev = "-".join(segments[:-1])
    segments[1] = stage
    prefix_now = "-".join(segments[:-1])
    ext = segments[-1].split(".")[1]
    skip = int(os.getenv('MODECT_SKIP_RATE'))

    idx = 1
    while idx < len(pics):
        if skip == 1 or idx % skip == 1:
            segments = pics[idx].split("-")
            segments[1] = stage
            shutil.move(input_dir + "/" + pics[idx],  \
                    output_dir + "/" + "-".join(segments))
        idx += 1

    # if one frame contains motion, hand all coming frames to the next stage, otherwise remove the frame
    pics = sorted(os.listdir(output_dir))
    for pic in pics:
        path = os.path.join(output_dir, pic)
        frame = cv2.imread(path, cv2.IMREAD_COLOR)
        if frame is None:
            print("failed to open picture %s" % path)
            os.rmdir(output_dir)
            return ''

        if last_gray is None:
            frame = imutils.resize(frame, width=320)
            last_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_gray = cv2.GaussianBlur(last_gray, (21, 21), 0)
            continue

        detected, gray = detect(last_gray, frame, min_area)
        if detected:
            break
        else:
            last_gray = gray
            os.remove(path)

    if len(os.listdir(output_dir)) == 0:
        os.rmdir(output_dir)
        return ''

    return output_dir

