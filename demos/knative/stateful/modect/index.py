import os
import time
from flask import Flask, request
import requests
from function import handler
app = Flask(__name__)

@app.route('/',methods=["POST"])
def hello_world():
    print(request.json)
    ret = handler.handle(request.json)
    service_url = os.getenv("NEXT_URL")
    
    # Send a POST request to the service with 'ret' as the JSON payload
    response = requests.post(service_url, json=ret)
    
    # Log the response status and content
    print(f"Response Status: {response.status_code}, Response Content: {response.text}")
    
    # Return the response from the remote service or the result from handler
    return response.text


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)