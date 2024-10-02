import os
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        # Handle POST request (e.g., reading JSON or form data)
        data = request.json  # Assuming a JSON body
        name = data.get('name', 'World')  # Get 'name' from the JSON body
        return f'Hello {name} via POST!\n'
    else:
        # Handle GET request (e.g., reading query parameters)
        name = request.args.get('name', 'World')  # Get 'name' query param
        return f'Hello {name} via GET!\n'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
