import json
import os
import subprocess
import time
import requests
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Replace with your Flask app's URL
URL_START = "http://"
URL_END = ".default.svc.cluster.local"

def make_request(i, function_name, writer, json_data):
    start_time = time.time()
    service_url = get_knative_service_url(function_name)
    print(f"Service URL is {service_url}")
    if service_url == None:
        print(f"URL for service {function_name} not found....skiping!!")
        return
    
    response = requests.post(service_url,  json=json_data)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Invocation {i+1} at {datetime.now().time()}: Status code {response.status_code}")
    writer.writerow([function_name, i+1, elapsed_time])
    if response.status_code == 200:
        try:
            # Try to parse the response text to JSON
            return json.loads(response.text)
        except json.JSONDecodeError:
            print("Error: Response is not valid JSON")
            return None
    else:
        print(f"Error: received status code {response.status_code}")
        return None

def get_knative_service_url(service_name):
    try:
        # Run the kubectl command to get the name and URL of the service
        result = subprocess.run(
            ['microk8s', 'kubectl', 'get', 'ksvc', service_name, '--output=custom-columns=NAME:.metadata.name,URL:.status.url'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Check if there was an error in the subprocess
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None

        # Process the output, skip the header line, and get the URL
        output = result.stdout.strip().split('\n')
        if len(output) < 2:
            print("No URL found for the service, cannot proceed exiting..!!!")
            os.exit(1)

        # The second line contains the name and URL
        name, url = output[1].split()
        return url
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def invoke_flask_app(limit, invocations, st):
    
    with open('response_times_knative_va_faas.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["functionName", "Invocation", "ResponseTime"])
        i = 0
        while time.time()  - st <= limit:
            i += 1
            prev_response = {"bucketName": "stage0", "fileName": "test_00.mp4"}
            # for function_name in function_names:
            response = make_request(i, "vidsplit", writer, json_data = prev_response)
            print(f"Final Response = {response}")

invoke_flask_app(limit=60, invocations=3, st=time.time())