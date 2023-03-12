from flask import Flask, send_from_directory, stream_with_context, request, g
from werkzeug.exceptions import HTTPException
import os, time, threading
from units import res, parse_body, Users

#from scan import scan_bp
from generator import generator_bp

app = Flask(__name__)

#app.register_blueprint(scan_bp)
app.register_blueprint(generator_bp)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 30
# 最大上传大小 30M
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['DATA_FOLDER'], 'user-upload')

users = Users(
    json_path = os.path.join(app.config['DATA_FOLDER'], "users.json")
)


@app.errorhandler(HTTPException)
def http_error(e):
    response = res(app, {
        'code': e.code,
        'message': e.name})
    response.status = e.code
    return response

@app.before_request
def authentication():
    if not request.path.startswith("/api/"): return None
    if "User-Id" in request.headers:
        g.user_id = request.headers['User-Id']
        g.user = users.get(g.user_id, {
            "imgs": [],
            "messages": []
        })
        g.users = users

        users[g.user_id] = g.user
    else:
        return res(app, {
            "code": -1,
            "message": "Authentication failed"
        })

@app.after_request
def save_users(res):
    if request.path.startswith("/api/"):
        users.save()
    return res

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/<path:file>')
def static_ui(file):
    return send_from_directory('ui', file)

@app.route('/user-upload/<path:file>')
def user_upload(file):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file)

@app.route('/api')
def api_index():
    return res(app, {
        'status': 'running',
        'version': '1.0.0'})

if __name__ == '__main__':
    app.run(port=3000, use_reloader=True)