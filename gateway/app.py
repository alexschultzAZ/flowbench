import io
import os
import requests
import templateparser
import json
from minio import Minio
from minio.error import S3Error

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.debug = True


ALLOWED_EXTENSIONS = set(['yml', 'yaml'])
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Downloads'))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1000 * 100  # 50 MB
app.config['CORS_HEADER'] = 'application/json'

minio_client = Minio("127.0.0.1:9000",    
        access_key="minioadmin",
        secret_key="minioadmin",
	    secure=False
    )


def allowedFile(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def init():
    print("gateway is healthy")
    return jsonify({"status": "success"})


@app.route('/uploadtemplate', methods=['POST'])
def uploadTemplate():
    file = request.files.getlist('files')[0]
    filename = secure_filename(file.filename)
    if allowedFile(filename):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        templateparser.process_template(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        return jsonify({'message': 'File type not allowed'}), 400
    return jsonify({"name": filename, "status": "success"})

# Create a bucket for storing the count if it doesn't exist
bucket_name = "async-counts"
if not minio_client.bucket_exists(bucket_name):
    minio_client.make_bucket(bucket_name)

"""
curl -X POST http://127.0.0.1:5000/async-handler \
-H "Content-Type: application/json" \
-d '{"functions_count": 3, "function_name": "func4"}'

"""

@app.route('/async-handler', methods=['POST'])
def handle_many_to_one_async():
    functions_count = request.args.get('functions_count')
    function_name = request.args.get('next_function')
    if not functions_count or not function_name:
        return jsonify({"message": "Invalid input"}), 400

    functions_count = int(functions_count)
    # Get the current count from MinIO
    try:
        count_object = minio_client.get_object(bucket_name, 'count.json')
        count_data = json.loads(count_object.read())
        count = count_data.get('count', 0)
    except S3Error as e:
        if e.code == 'NoSuchKey':
            count = 0
        else:
            raise

    # Increment the count
    count += 1


    # Update the count in MinIO
    count_data = {'count': count}
    count_data_str = json.dumps(count_data)
    count_data_bytes = io.BytesIO(count_data_str.encode('utf-8'))

    minio_client.put_object(
        bucket_name,
        'count.json',
        data=count_data_bytes,
        length=len(count_data_str),
        content_type='application/json'
    )
    print("Function count = {}, count = {}".format(functions_count, count))

    # Check if the count matches the number of expected functions
    if count == functions_count:
        print("Yesss condition satisfied")
        # All functions have successfully run, proceed to call the next function
        # Simulating the function call
        response = requests.get("http://127.0.0.1:8080/function/" + function_name)
        print(f"Called the function at level 2 {function_name} successfully")

        #Clear the count bucket for next invocations
        count_data = {'count': 0}
        count_data_str = json.dumps(count_data)
        count_data_bytes = io.BytesIO(count_data_str.encode('utf-8'))

        minio_client.put_object(
            bucket_name,
            'count.json',
            data=count_data_bytes,
            length=len(count_data_str),
            content_type='application/json'
        )
        print("Cleared the async_counts for future new invocations")
        return jsonify({"message": f"Level 2 function {function_name} called successfully"}), 200

    return jsonify({"message": "Callback received, still counts not reached"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
