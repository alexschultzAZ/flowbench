from flask import Flask, request
app = Flask(__name__)

from vidsplit import vidsplit_handler
from modect.function import modect_handler
from facextract.function import facextract_handler
from facerec.function import facerec_handler

def handle(req):
    output1 = vidsplit_handler.handle(req)
    output2 = modect_handler.handle(output1)
    output3 = facextract_handler.handle(output2)
    output4 = facerec_handler.handle(output3)
    return output4

@app.route('/',methods=["POST"])
def hello_world():
    print(request.json)
    ret = handle(request.json)
    return ret

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)