from flask import Flask, send_from_directory, request, g
from werkzeug.exceptions import HTTPException
from units import res, Users
from ocr import Image2Document
import os, time

app = Flask(__name__)

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
            "imgs": []
        })
        
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

@app.route('/api/upload_imgs', methods=['POST'])
def upload_imgs():
    user_imgs = users[g.user_id]["imgs"]
    for file in request.files.getlist('file'):
        name, ext = os.path.splitext(file.filename)
        filename = '{}-{}{}'.format(g.user_id, str(len(user_imgs) + 1), ext)
        
        user_imgs.append({
            "url": "/user-upload/" + filename
        })
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return res(app, user_imgs)

@app.route('/api/get_imgs_list')
def get_imgs_list():
    return res(app, g.user["imgs"])

@app.route('/api/scan_imgs')
def scan_imgs():
    pages = []
    for img in g.user["imgs"]:
        # 加一个点，将URL的根目录转为文件系统相对路径
        document = Image2Document('.' + img["url"])
        img["document"] = document
        pages.append(document)
    return res(app, pages)

@app.route('/api')
def api_index():
    return res(app, {
        'status': 'running',
        'version': '1.0.0'})

if __name__ == '__main__':
    app.run(port=3000, use_reloader=True)