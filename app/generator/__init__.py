from flask import Blueprint, current_app, stream_with_context, request, g
import threading
from concurrent.futures import ThreadPoolExecutor
from units import res, parse_body
from .answer import AnswersGenerator

generator_bp = Blueprint('Generator', __name__)

@generator_bp.route('/generate_prompt', methods=['POST'])
def generate_prompt():
    body = parse_body(request, {})
    body.setdefault("imgs", g.user.imgs)
    # 未指定需要处理的页数就遍历全部图片
    body.setdefault("indexs", list(range(len(body["imgs"]))))
    full_document = ""
    for index in body["indexs"]:
        img = body["imgs"][index]
        full_document += img.get("document_text", "")
    
    prompt = AnswersGenerator.generatePrompt(full_document)
    return res(current_app, {'prompt': prompt})

executor = ThreadPoolExecutor(max_workers=2)
lock = threading.Lock()

def thinking_bgtask(user, message):
    generator = AnswersGenerator(user.messages)
    generator.send(message)
    for text_snippet in generator.generate():
        yield text_snippet
    with lock:
        # 更新 用户数据 中的 消息列表
        user.messages = generator.messages
        user.messages_status = "waiting"
        g.users.save()

@generator_bp.route('/send', methods=['POST'])
def generator_send():
    message = {"role": "user", "content": request.data.decode()}
    message.tag = request.args.get('tag')
    
    bgtask = executor.submit(thinking_bgtask,
        g.user, message)
    g.user.messages_status = "thinking"
    
    def stream():
        yield ""
        for result in bgtask.result():
            yield result
    return stream_with_context(stream())


@generator_bp.route('/messages')
def generator_messages():
    return res(current_app, g.user.messages)

@generator_bp.route('/clear')
def generator_clean():
    g.user.messages = []
    return res(current_app, [])
