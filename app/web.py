from flask import Flask, send_from_directory, request, g
from werkzeug.exceptions import HTTPException
from units import res, parse_body, Users
from scan import Image2Document
from answer import AnswersGenerater
import os, time, threading

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
            "imgs": [],
            "messages": []
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

lock = threading.Lock()
# 设置最大线程数为 2
semaphore = threading.BoundedSemaphore(2)

def ScanImgAndSave(img):
    semaphore.acquire()
    # 连接 "data" 将URL的根目录转为文件系统相对路径
    result = Image2Document('data' + img["url"])
    # 在锁中进行用户数据、文件系统操作
    with lock:
        img["document"] = result
        img["document_status"] = "finished"
        users.save()
        print(img["url"], "saved")
        pass
    semaphore.release()

@app.route('/api/scan_imgs')
def scan_imgs():
    for img in g.user["imgs"]:
        doc = img.get("document")
        if doc is None:
            document_thread = threading.Thread(target=ScanImgAndSave,
                args=(img,),
                daemon=True)
            document_thread.start()
            img["document_status"] = "doing"
            print("scan_imgs", threading.enumerate())
    return res(app, g.user["imgs"])

@app.route('/api/generate_prompt', methods=['POST'])
def generate_prompt():
    body = parse_body(request)
    body.setdefault("imgs", g.user["imgs"])
    # 未指定需要处理的页数就遍历全部图片
    body.setdefault("indexs", range(len(body["imgs"])))
    document = []
    for index in body["indexs"]:
        img = body["imgs"][index]
        document += img.get("document")
    
    prompt = AnswersGenerater.generatePrompt(document)
    return res(app, {'prompt': prompt})


@app.route('/api/generater/send', methods=['POST'])
def generater_send():
    # 从 用户数据 的 消息列表 中初始化 AnswersGenerater
    generater = AnswersGenerater(g.user["messages"])
    generater.send(request.data.decode())
    last_message = generater.generate()
    # 获取到 AI 回复后更新 用户数据 中的 消息列表
    g.user["messages"] = generater.messages
    return res(app, last_message)

@app.route('/api/generater/messages')
def generater_messages():
    return res(app, g.user["messages"])

@app.route('/api/generater/clean')
def generater_clean():
    g.user["messages"] = []
    return res(app, {'message': 'ok'})


@app.route('/api')
def api_index():
    return res(app, {
        'status': 'running',
        'version': '1.0.0'})

if __name__ == '__main__':
    app.run(port=3000, use_reloader=True)