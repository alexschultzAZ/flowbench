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
import csv
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Replace with your Flask app's URL
FLASK_APP_URL = "http://localhost:8080/function/"
function_name = 'va-stateful-vidsplit'
def make_request(i, writer):
    try:
        start_time = time.time()
        response = requests.post(FLASK_APP_URL + function_name, data="bucketName=stage0&fileName=test_00.mp4")
        end_time = time.time()

        elapsed_time = end_time - start_time
        print(f"Invocation {i+1} at {datetime.now().time()}: Status code {response.status_code}")
        writer.writerow([i+1, elapsed_time])
    except requests.RequestException as e:
        print(f"Invocation {i+1} at {datetime.now().time()}: Request failed: {e}")
        writer.writerow([i+1, "Failed"])

def invoke_flask_app(limit, invocations, st):
    # interval = (minutes * 60) / invocations  # Calculate the interval in seconds
    
    with open('response_times_va-stateful-gpu.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Invocation", "ResponseTime"])
        
        for i in range(invocations):
            if time.time()  - st > limit:
                break
            make_request(i, writer)

# Replace these values with your desired number of minutes and invocations
invoke_flask_app(limit=60, invocations=100, st = time.time())

