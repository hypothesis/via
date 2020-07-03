import json
from collections import OrderedDict

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def dump_headers():
    headers = OrderedDict(request.headers)

    for bad_header in ('Cookie', 'Host'):
        headers.pop(bad_header, None)

    return f"<pre>{json.dumps(headers, indent=4)}</pre>", 200


if __name__ == '__main__':
    app.run(debug=True)