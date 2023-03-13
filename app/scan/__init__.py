from flask import Blueprint, current_app, stream_with_context, request, g
import os, threading, json
from concurrent.futures import ThreadPoolExecutor
from units import res
from .scan import Image2Document

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/api/upload_imgs', methods=['POST'])
def upload_imgs():
    user_imgs = g.user["imgs"]
    for file in request.files.getlist('file'):
        name, ext = os.path.splitext(file.filename)
        filename = '{}-{}{}'.format(g.user_id, str(len(user_imgs) + 1), ext)
        
        user_imgs.append({
            "url": "/user-upload/" + filename,
            "document_status": "unscanned"
        })
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return res(current_app, user_imgs)

@scan_bp.route('/api/get_imgs_list')
def get_imgs_list():
    res_list = g.user["imgs"].copy()
    if not request.args.get("docments"):
        for img in res_list:
            if 'document' in img:
               del img['document']
    return res(current_app, res_list)

executor = ThreadPoolExecutor(max_workers=2)
lock = threading.Lock()

def scanning_bgtask(img):
    doc = img.get("document")
    if doc is not None: return doc
    
    # 连接 "data" 将URL的根目录转为文件系统相对路径
    result = Image2Document('data' + img["url"])
    # 在锁中进行用户数据、文件系统操作
    with lock:
        img["document"] = result
        img["document_status"] = "scanned"
        users.save()
    return json.dumps(result)

@scan_bp.route('/api/scan_imgs')
def scan_imgs():
    tasks = []
    for img in g.user["imgs"]:
        tasks.append(executor.submit(scanning_bgtask, img))
        img["document_status"] = "scanning"
    
    def stream():
        yield "start"
        for task in tasks:
            yield task.result()
    return stream_with_context(stream())


