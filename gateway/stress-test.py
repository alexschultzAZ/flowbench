import asyncio
import json
import os
import subprocess
import time
import aiohttp
import csv
from datetime import datetime
import openpyxl
import json

def write_to_workbook(responses):
    

    # Parse JSON responses
    valid_responses = []

    for response in responses:
        try:
            if response:  # Check if the response is not empty
                # If the response is already a dictionary, no need to load it again
                if isinstance(response, str):
                    parsed_response = json.loads(response)  # Parse string response
                elif isinstance(response, dict):
                    parsed_response = response  # Use the dict as is
                else:
                    print(f"Warning: Unexpected response type {type(response)}")
                    continue

                valid_responses.append(parsed_response)
            else:
                print("Warning: Empty response received")
        except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
            print(f"Error parsing response: {e}")

    # Create an Excel workbook and sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "End-To-End Time"

    # Add headers
    sheet.append(["Invocation", "Total Time"])

    # Add data
    for i, response in enumerate(valid_responses, start=1):
        total_time = response.get("total_time", None)  # Default to None if total_time not found
        sheet.append([i, total_time])

    # Save the workbook
    excel_file = "invocation_total_times.xlsx"
    workbook.save(excel_file)
    print(f"Excel sheet '{excel_file}' created successfully!")

# async def make_request(current_invocation, service_url, session):
    
    
#     json_data = {"bucketName": "stage0", "fileName": "test_00.mp4"}
#     async with session.post(url=service_url, json=json_data) as response:
#         # elapsed_time = response.elapsed.total_seconds() if response.elapsed else 0
#         # print(f"Invocation {current_invocation + 1} at {datetime.now().time()}: Status code {response.status}")
#         if response.status == 200:
#             try:
#                 return await response.text()
#             except aiohttp.ContentTypeError:
#                 print("Error: Response is not valid JSON")
#                 return None
#         else:
#             print(f"Error: received status code {response.status}")
#             return None
async def make_request(current_invocation, service_url, session):
    json_data = {"bucketName": "stage0", "fileName": "test_00.mp4"}
    async with session.post(url=service_url, json=json_data) as response:
        # Check for a successful response
        if response.status == 200:
            try:
                # Attempt to parse the response as JSON
                response_text = await response.text()
                if response_text:  # Only parse if the response text is not empty
                    return json.loads(response_text)
                else:
                    print(f"Error: Empty response for invocation {current_invocation}")
                    return None
            except aiohttp.ContentTypeError:
                print(f"Error: Response is not valid JSON for invocation {current_invocation}")
                return None
            except json.JSONDecodeError:
                print(f"Error: Failed to decode JSON for invocation {current_invocation}")
                return None
        else:
            print(f"Error: Received status code {response.status} for invocation {current_invocation}")
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
        invocation = 0
        start_time = time.time()
        now = datetime.now()
        start_date_time = now.strftime("%A, %d %B %Y, %I:%M:%S %p")
        print(f'Start Date Time is {start_date_time}')
        while invocation < invocations:
            invocation += 1
            tasks.append(asyncio.ensure_future(make_request(invocation, service_url, session)))
            
        print(f'Total invocations done are {invocation}')
        responses = await asyncio.gather(*tasks)
        # print(responses)

        end_time = time.time()
        
        print(f'Total time took is {end_time - start_time}')
        # write_to_workbook(responses)
        # print(responses)

if __name__ == "__main__":
    # invocation_count = 
    asyncio.run(invoke_flask_app(3))
