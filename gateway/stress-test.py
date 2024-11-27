import asyncio
import json
import os
import subprocess
import time
import aiohttp
import csv
from datetime import datetime

async def make_request(current_invocation, service_url, session):
    
    
    json_data = {"bucketName": "stage0", "fileName": "test_00.mp4"}
    async with session.post(url=service_url, json=json_data) as response:
        # elapsed_time = response.elapsed.total_seconds() if response.elapsed else 0
        # print(f"Invocation {current_invocation + 1} at {datetime.now().time()}: Status code {response.status}")
        if response.status == 200:
            try:
                return await response.text()
            except aiohttp.ContentTypeError:
                print("Error: Response is not valid JSON")
                return None
        else:
            print(f"Error: received status code {response.status}")
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

async def invoke_flask_app(invocations):
    function_name = "vidsplit"
    service_url = get_knative_service_url(function_name)
    # print(f"Service URL is {service_url}")
    if service_url is None:
        print(f"URL for service {function_name} not found.... skipping!!")
        return
    # for i in range(100000):
    #     print(time.time() - start_time)
    async with aiohttp.ClientSession() as session:
        tasks = []
        invocation = 1
        start_time = time.time()
        while invocation < invocations:
            tasks.append(asyncio.ensure_future(make_request(invocation, service_url, session)))
            invocation += 1
        print(f'Total invocations done are {invocation}')
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        print(f'Total time took is {end_time - start_time}')
        # print(responses)

if __name__ == "__main__":
    # invocation_count = 
    asyncio.run(invoke_flask_app(20))
