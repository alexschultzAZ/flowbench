import time
import requests
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Replace with your Flask app's URL
FLASK_APP_URL = "http://localhost:8080/function/"

def make_request(i, function_name, writer, data):
    start_time = time.time()
    response = requests.post(FLASK_APP_URL + function_name, data=data)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Invocation {i+1} at {datetime.now().time()}: Status code {response.status_code}")
    writer.writerow([function_name, i+1, elapsed_time])
    return response.text

def invoke_flask_app(limit, invocations, st):
    function_names = ["vidsplit", "modect", "facextract", "facerec"]

    with open('response_times_va_faas.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["functionName", "Invocation", "ResponseTime"])
        i = 0
        while time.time()  - st <= limit:
            i += 1
            prev_response = "bucketName=stage0&fileName=test_00.mp4"
            for function_name in function_names:
                prev_response = make_request(i, function_name, writer, data = prev_response)

# Replace these values with your desired number of minutes and invocations
invoke_flask_app(limit=60, invocations=3, st=time.time())