import requests
import json
import time

url = "http://knative-vidsplit.default.10.64.140.43.sslip.io"
headers = {"Content-Type": "application/json"}
data = {"bucketName": "stage0", "fileName": "test_00.mp4"}

def make_requests():
    start_time = time.time()
    duration = 60  # 1 minute
    request_count = 0

    while time.time() - start_time < duration:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        request_count += 1
        print(f"Request {request_count}: Status Code: {response.status_code}")

if __name__ == "__main__":
    make_requests()