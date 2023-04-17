from flask import Blueprint, current_app, stream_with_context, request, g
from concurrent.futures import ThreadPoolExecutor
import json
from units import res, parse_body, Message
from .answer import AnswersGenerator

generator_bp = Blueprint('Generator', __name__)

@generator_bp.route('/generate_prompt', methods=['POST'])
def generate_prompt():
    body = parse_body(request, {})
    body.setdefault("imgs", g.user.imgs)
    # 未指定需要处理的页数就遍历全部图片
    body.setdefault("indexs", list(range(len(body["imgs"]))))
    full_document = ""
    for index in reversed(body["indexs"]):
        img = body["imgs"][index]
        full_document += getattr(img, "document_text") or ""
    
    prompt = AnswersGenerator.generatePrompt(full_document)
    return res(current_app, {'prompt': prompt})

executor = ThreadPoolExecutor(max_workers=2)

def thinking_bgtask(message):
    dict_messages = [msg.as_dict() for msg in g.user.messages]
    before_length = len(dict_messages)

    generator = AnswersGenerator(dict_messages if dict_messages else None)

    generator.send(message.as_dict())
    for text_snippet in generator.generate():
        yield text_snippet

    # 切片获取发送后新增的几条消息
    new_messages = generator.messages[before_length:]
    print(new_messages)
    # 向数据库中新增消息
    for message in new_messages:
        g.db_session.add(Message(
            role=message.get("role"),
            content=message.get("content"),
            tag=message.get("tag"),
            user=g.user))
    g.db_session.commit()

@generator_bp.route('/send', methods=['POST'])
def generator_send():
    message = Message(
        role="user",
        content=request.data.decode(),
        tag=request.args.get('tag'),
        user=g.user
    )
    
    bgtask = executor.submit(thinking_bgtask, message)
    
    def stream():
        yield ""
        for text_snippet in bgtask.result():
            yield text_snippet
    return stream_with_context(stream())


@generator_bp.route('/messages')
def generator_messages():
    return res(current_app, [item.as_dict() for item in g.user.messages])

@generator_bp.route('/clear')
def generator_clean():
    for msg in g.user.messages:
        g.db_session.delete(msg)
    return res(current_app, [])
