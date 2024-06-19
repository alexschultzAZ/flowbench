import face_recognition
import json
from minio import Minio
import numpy as np
import cv2  # Import OpenCV
import os

# Initialize MinIO client using environment variables
minio_client = Minio(
    os.getenv('MINIO_ADDR'),
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=False
)

# Assuming known_face_encodings is initially empty


def load_known_face_encodings():
    try:
        known_face_encodings = []

        # List objects in 'known-faces' bucket
        objects = minio_client.list_objects('known-faces')
        print('objects')
        for obj in objects:
            print('inside')
            # Get object data from MinIO
            response = minio_client.get_object('known-faces', obj.object_name)
            # Read image data
            data = response.read()
            # print(' data is ', data)
            # Convert image data to numpy array
            image_array = np.frombuffer(data, np.uint8)

            # Decode image using OpenCV
            face_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            # Convert image to RGB if it's not already in RGB format
            if len(face_image.shape) < 3 or face_image.shape[2] != 3:
                face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            print('loaded')
            # Perform face encoding
            face_encoding = face_recognition.face_encodings(face_image)[0]  # Assuming only one face in the image
            known_face_encodings.append(face_encoding)
            print('after loaded')
            # Close the response to release resources
            response.close()
            # Release the connection associated with the response
            response.release_conn()
            return known_face_encodings

    except Exception as e:
        return "Exception" + str(e)


def handle():
    known_face_encodings = load_known_face_encodings()
    # faces_bucket = 'stage2'
    # objects = minio_client.list_objects(faces_bucket)

    results = []

    # for obj in objects:
    #     try:
    #         # Get object data from MinIO
    #         response = minio_client.get_object(faces_bucket, obj.object_name)
    #         # Read image data
    #         data = response.read()

    #         # Convert image data to numpy array
    #         image_array = np.frombuffer(data, np.uint8)

    #         # Decode image using OpenCV
    #         face_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    #         # Convert image to RGB if it's not already in RGB format
    #         if len(face_image.shape) < 3 or face_image.shape[2] != 3:
    #             face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

    #         # Perform face recognition
    #         face_encodings = face_recognition.face_encodings(face_image)

    #         for face_encoding in face_encodings:
    #             print('known is ', known_face_encodings)
    #             matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
    #             results.append(matches)

    #     except Exception as e:
    #         return str(e)
    #     finally:
    #         # Close the response to release resources
    #         response.close()
    #         # Release the connection associated with the response
    #         response.release_conn()

    return json.dumps({"results": results})

# Example invocation (assuming your handler expects no arguments)
result = handle()
print(result)
