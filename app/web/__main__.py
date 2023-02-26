from flask import Flask, send_from_directory, request
from werkzeug.exceptions import HTTPException
from .units import response as res
import os, time

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 30
# 最大上传大小 30M
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'user-upload')

@app.errorhandler(HTTPException)
def http_error(e):
    response = res(app, {
        'code': e.code,
        'message': e.name})
    response.status = e.code
    return response

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/<path:file>')
def serve_results(file):
    return send_from_directory('ui', file)

@app.route('/upload', methods=['POST'])
def upload_imgs():
    for index, file in enumerate(request.files.getlist('file')):
        name, ext = os.path.splitext(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],
            '{}-{}{}'.format(request.headers['User-Id'], str(index), ext)))
    return res(app, {'message': 'ok'})

@app.route('/api')
def api_index():
    return res(app, {
        'status': 'running',
        'version': '1.0.0'})

app.run(port=3000, use_reloader=True)