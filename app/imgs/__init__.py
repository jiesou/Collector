from flask import Blueprint, current_app, stream_with_context, request, g
import os, json
from concurrent.futures import ThreadPoolExecutor
from units import res, Img
from .scan_plaintext import Image2Document

imgs_bp = Blueprint('imgs', __name__)

@imgs_bp.route('/upload', methods=['POST'])
def upload_imgs():
    user_imgs = g.user.imgs
    new_imgs = []
    for file in request.files.getlist('file'):
        name, ext = os.path.splitext(file.filename)
        filename = f'{g.user_id}-{len(user_imgs)}{ext}'
        
        img = Img(
            url="/user-upload/" + filename,
            document_status="unscanned",
            user=g.user
        )
        g.db_session.add(img)
        new_imgs.append(img.as_dict())
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
    return res(current_app, new_imgs)

@imgs_bp.route('/list')
def get_imgs_list():
    imgs = g.user.imgs
    res_list = [img.as_dict() for img in imgs]
    if not request.args.get("documents"):
        for img in res_list:
            if hasattr(img, 'document_text'):
               del img.document_text
    
    return res(current_app, res_list)

@imgs_bp.route('/delete/<int:index>')
def delete_img(index):
    if index < len(g.user.imgs):
        try:
          # 连接 "data" 将URL的根目录转为文件系统相对路径
          os.remove('data' + g.user.imgs[index].url)
        except: pass
        g.db_session.delete(g.user.imgs[index])
    return get_imgs_list()

executor = ThreadPoolExecutor(max_workers=2)

def scanning_bgtask():
    for img in g.user.imgs:
        result = img.document_text
        if result is None:
            result = Image2Document('data' + img.url)
            
            # img["document"] = result
            img.document_text = result
            img.document_status = "scanned"
            g.db_session.commit()
        yield json.dumps(img.as_dict())

@imgs_bp.route('/scan')
def scan_imgs():
    bgtask = executor.submit(scanning_bgtask)
    
    def stream():
        yield ""
        for document in bgtask.result():
            yield f"{document}\n"
    return stream_with_context(stream())


