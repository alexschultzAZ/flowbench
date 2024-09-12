import torch
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def check_gpu():

    acceleration = os.getenv('ACCELERATION', 'cpu')
    print("Acceleration os getenv is ", acceleration)
    if acceleration == 'gpu':

        if torch.cuda.is_available():
            return "GPU is available!\n"
        else:
            return "GPU is not available.\n"
    else:
        return "Using CPU"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
