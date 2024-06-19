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

    stage1_bucket = 'stage1'
    stage2_bucket = 'stage2'

    # Ensure stage2 bucket exists, create if not
    if not minio_client.bucket_exists(stage2_bucket):
        minio_client.make_bucket(stage2_bucket)

    # Process frames from stage1 bucket
    try:
        # List objects in stage1 bucket
        objects = minio_client.list_objects(stage1_bucket)

        for obj in objects:
            frame_file = obj.object_name

            # Download frame from stage1 bucket
            temp_frame = tempfile.NamedTemporaryFile(delete=False)
            try:
                minio_client.fget_object(stage1_bucket, frame_file, temp_frame.name)

                # Perform face extraction (example: using OpenCV's Haar Cascade Classifier)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                frame = cv2.imread(temp_frame.name)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

                # Save extracted faces to stage2 bucket
                for (x, y, w, h) in faces:
                    face_filename = f"{uuid.uuid4()}.jpg"
                    face_path = os.path.join('/tmp', face_filename)
                    cv2.imwrite(face_path, frame[y:y+h, x:x+w])

                    try:
                        with open(face_path, 'rb') as data:
                            minio_client.put_object(stage2_bucket, face_filename, data, length=os.stat(face_path).st_size)
                    except S3Error as e:
                        return str(e)

                    # Clean up: remove temporary face file
                    os.remove(face_path)

                # Clean up: remove temporary frame file
                temp_frame.close()
                os.remove(temp_frame.name)

            except S3Error as e:
                return str(e)

        return "Face extraction and upload to stage2 completed successfully"

    except S3Error as e:
        return str(e)

# Example invocation (assuming your handler expects no arguments)
result = handle()
print(result)
