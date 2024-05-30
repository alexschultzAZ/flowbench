import os
import requests
import templateparser


from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.debug = True


ALLOWED_EXTENSIONS = set(['yml', 'yaml'])
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Downloads'))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1000 * 100  # 50 MB
app.config['CORS_HEADER'] = 'application/json'


def allowedFile(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def init():
    print("gateway is healthy")
    return jsonify({"status": "success"})


@app.route('/uploadtemplate', methods=['POST'])
def uploadTemplate():
    file = request.files.getlist('files')[0]
    filename = secure_filename(file.filename)
    if allowedFile(filename):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        templateparser.process_template(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        return jsonify({'message': 'File type not allowed'}), 400
    return jsonify({"name": filename, "status": "success"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
