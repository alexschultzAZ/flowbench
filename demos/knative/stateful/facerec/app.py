import os
from flask import Flask, request
from function import handler
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        # Handle POST request (e.g., reading JSON or form data)
        data = request.json  # Assuming a JSON body
        ret = handler.handle(req=data)
        if ret != None:
            print(ret)
        return ret
    else:
        return "Hello, World!"
        


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
