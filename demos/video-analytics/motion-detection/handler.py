import cv2
import tempfile
from minio import Minio
import os
import numpy as np
from io import BytesIO

def handle(req):
    minio_client = Minio(
            os.getenv('MINIO_ADDR'),
            access_key=os.getenv('MINIO_ACCESS_KEY'),
            secret_key=os.getenv('MINIO_SECRET_KEY'),
            secure=False
    )
    bucket_name = 'video-frames'
    objects = minio_client.list_objects(bucket_name)

    frame_files = []
    for obj in objects:
        frame_files.append(obj.object_name)
    
    frame_files.sort()  # Assuming frames are uploaded in sequence

    if len(frame_files) < 2:
        return "Not enough frames for motion detection"

    ret, frame1 = minio_client.get_object(bucket_name, frame_files[0])
    ret, frame2 = minio_client.get_object(bucket_name, frame_files[1])

    frame1 = np.asarray(bytearray(frame1.read()), dtype="uint8")
    frame2 = np.asarray(bytearray(frame2.read()), dtype="uint8")

    frame1 = cv2.imdecode(frame1, cv2.IMREAD_COLOR)
    frame2 = cv2.imdecode(frame2, cv2.IMREAD_COLOR)

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (frame1.shape[1], frame1.shape[0]))

    for i in range(2, len(frame_files)):
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 25, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)

        out.write(frame1)

        frame1 = frame2
        ret, frame2 = minio_client.get_object(bucket_name, frame_files[i])
        frame2 = np.asarray(bytearray(frame2.read()), dtype="uint8")
        frame2 = cv2.imdecode(frame2, cv2.IMREAD_COLOR)

    out.release()

    with open(output_path, 'rb') as f:
        video_data = f.read()

    os.remove(output_path)

    return video_data
