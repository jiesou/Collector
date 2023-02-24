from flask import Flask, send_from_directory, request
from werkzeug.exceptions import HTTPException
from .units import response as res
import os, time

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 30
# 最大上传大小 30M

@app.errorhandler(HTTPException)
def http_error(e):
    res = e.get_res()
    res.data = res(app, {
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
    date = time.strftime("%H:%M:%S", time.localtime(int(request.headers['X-Timestamp'])))
    print(request.files.getlist('file'))
    for index, file in zip(request.files.getlist('file')):
      print(os.path.join('user-upload', date, str(index)))
      if file.filename != '':
          file.save(os.path.join('user-upload', date, str(index)))
    return res(app, {'message': 'ok'})

@app.route('/api')
def api_index():
    return res(app, {
        'status': 'running',
        'version': '1.0.0'})

app.run(port=3000, use_reloader=True)