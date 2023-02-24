from flask import Flask, send_from_directory, request
from werkzeug.exceptions import HTTPException
from .units import response

app = Flask(__name__)

@app.errorhandler(HTTPException)
def http_error(e):
    res = e.get_response()
    res.data = response(app, {
        'code': e.code,
        'message': e.name}).data
    res.content_type = 'application/json'
    return res

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/<path:file>')
def serve_results(file):
    return send_from_directory('ui', file)

@app.route('/upload', methods=['POST'])
def upload_imgs():
    file = request.files['file']
    if file.filename != '':
        file.save(file.filename)
    return redirect('/')

@app.route('/api')
def api_index():
    return response(app, {
        'status': 'running',
        'version': '1.0.0'})

app.run(port=3000, use_reloader=True)