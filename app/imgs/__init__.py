from flask import Blueprint, current_app, stream_with_context, request, g
import os, threading, json, copy
from concurrent.futures import ThreadPoolExecutor
from units import res
from .scan_plaintext import Image2Document

imgs_bp = Blueprint('imgs', __name__)

@imgs_bp.route('/upload', methods=['POST'])
def upload_imgs():
    user_imgs = g.user["imgs"]
    for file in request.files.getlist('file'):
        name, ext = os.path.splitext(file.filename)
        filename = f'{g.user_id}-{len(user_imgs)}{ext}'
        
        user_imgs.append({
            "url": "/user-upload/" + filename,
            "document_status": "unscanned"
        })
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return res(current_app, user_imgs)

@imgs_bp.route('/list')
def get_imgs_list():
    res_list = g.user["imgs"]
    if not request.args.get("documents"):
        res_list = copy.deepcopy(res_list)
        for img in res_list:
            if 'document_text' in img:
               del img['document_text']
    return res(current_app, res_list)

@imgs_bp.route('/delete/<int:index>')
def delete_img(index):
    if index < len(g.user["imgs"]):
        try:
          # 连接 "data" 将URL的根目录转为文件系统相对路径
          os.remove('data' + g.user["imgs"][index]["url"])
        except: pass
        g.user["imgs"].pop(index)
    return get_imgs_list()

executor = ThreadPoolExecutor(max_workers=2)
lock = threading.Lock()

def scanning_bgtask():
    for img in g.user["imgs"]:
        result = img.get("document_text")
        if result is None:
            result = Image2Document('data' + img["url"])
            
            # img["document"] = result
            img["document_text"] = result
            img["document_status"] = "scanned"
            # 在锁中进行用户数据、文件系统操作
            with lock:
                g.users.save()
        yield json.dumps(result)

@imgs_bp.route('/scan')
def scan_imgs():
    bgtask = executor.submit(scanning_bgtask)
    
    def stream():
        yield ""
        for document in bgtask.result():
            yield f"{document}\n"
    return stream_with_context(stream())


