# import time
# import requests
# from datetime import datetime

# # Replace with your Flask app's URL
# FLASK_APP_URL = "http://localhost:8080/function/"

# def invoke_flask_app(minutes, invocations):
#     interval = (minutes * 60) / invocations  # Calculate the interval in seconds
#     function_name = "va-monolith"
#     for i in range(invocations):
#         response = requests.post(FLASK_APP_URL + function_name, data= "bucketName=stage0&fileName=test_00.mp4")
#         print(f"Invocation {i+1} at {datetime.now().time()}: Status code {response.status_code}")
#         # time.sleep(interval)

# # Replace these values with your desired number of minutes and invocations
# invoke_flask_app(minutes=1, invocations=5)
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Replace with your Flask app's URL
FLASK_APP_URL = "http://localhost:8080/function/"

def make_request(i, function_name):
    response = requests.post(FLASK_APP_URL + function_name, data= "bucketName=stage0&fileName=test_00.mp4")
    print(f"Invocation {i+1} at {datetime.now().time()}: Status code {response.status_code}")

def invoke_flask_app(minutes, invocations):
    interval = (minutes * 60) / invocations  # Calculate the interval in seconds
    function_name = "va-monolith"

    with ThreadPoolExecutor(max_workers=5) as executor:
        for i in range(invocations):
            executor.submit(make_request, i, function_name)
            # time.sleep(interval)

# Replace these values with your desired number of minutes and invocations
invoke_flask_app(minutes=1, invocations=30)