import cv2
import os
import uuid
from minio import Minio
from minio.error import S3Error
import tempfile

def handle():
    # Initialize MinIO client
    minio_client = Minio(
        os.getenv('MINIO_ADDR'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

    stage0_bucket = 'stage0'
    stage1_bucket = 'stage1'
    if not minio_client.bucket_exists(stage1_bucket):
        minio_client.make_bucket(stage1_bucket)
    video_filename = 'test_00.mp4'  # Replace with your actual video file name

    # Create a temporary file to store the downloaded video
    temp_video = tempfile.NamedTemporaryFile(delete=False)
    try:
        # Download video file from stage0 bucket
        minio_client.fget_object(stage0_bucket, video_filename, temp_video.name)

        # Open the downloaded video file
        video_capture = cv2.VideoCapture(temp_video.name)
        success, frame = video_capture.read()
        count = 0

        # Process each frame in the video
        while success:
            frame_filename = f"{uuid.uuid4()}.jpg"
            frame_path = os.path.join('/tmp', frame_filename)
            cv2.imwrite(frame_path, frame)

            try:
                # Upload frame to stage1 bucket
                with open(frame_path, 'rb') as data:
                    minio_client.put_object(stage1_bucket, frame_filename, data, length=os.stat(frame_path).st_size)
            except S3Error as e:
                return str(e)

            # Clean up: remove the temporary frame file
            os.remove(frame_path)

            # Read the next frame
            success, frame = video_capture.read()
            count += 1

        # Release resources
        video_capture.release()

        return f"Total frames extracted and uploaded to stage1: {count}"
    
    finally:
        # Clean up: remove the temporary video file
        temp_video.close()
        os.remove(temp_video.name)

# Call the handle function to start processing the video
result = handle()
print(result)
