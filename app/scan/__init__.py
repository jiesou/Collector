from flask import Blueprint, current_app, stream_with_context, request, g
import threading
from units import res
from .scan import Images2Docment

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/api/upload_imgs', methods=['POST'])
def upload_imgs():
    user_imgs = users[g.user_id]["imgs"]
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
        img["document_status"] = "scanned"
        users.save()
        print(img["url"], "saved")
        pass
    semaphore.release()

@scan_bp.route('/api/scan_imgs')
def scan_imgs():
    for img in g.user["imgs"]:
        doc = img.get("document")
        if doc is None:
            document_thread = threading.Thread(target=ScanImgAndSave,
                args=(img,),
                daemon=True)
            document_thread.start()
            img["document_status"] = "scanning"
            print("scan_imgs", threading.enumerate())
    return res(current_app, g.user["imgs"])


