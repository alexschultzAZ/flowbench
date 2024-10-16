import os
import time
from flask import Flask, request
import requests
from function import handler
app = Flask(__name__)

@app.route('/',methods=["POST"])
def hello_world():
    # print(request.json)
    ret = handler.handle(request.json)

    
    # Return the response from the remote service or the result from handler
    return ret

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)