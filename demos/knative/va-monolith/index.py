import time
from flask import Flask, request
from function import handler
app = Flask(__name__)

@app.route('/',methods=["POST"])
def hello_world():
    print(request.json)
    ret = handler.handle(request.json)
    return ret

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)