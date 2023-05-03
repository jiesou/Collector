from flask import Blueprint, current_app, stream_with_context, request, g
from sqlalchemy.orm import scoped_session
from concurrent.futures import ThreadPoolExecutor
from units import res, parse_body, Message, User
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

executor = ThreadPoolExecutor(max_workers=8)

def thinking_bgtask(message, user):
    with current_app.app_context():
        db_session = scoped_session(current_app.db_session_factory)
        old_dict_messages = [msg.as_dict() for msg in user.messages]
        generator = AnswersGenerator(old_dict_messages if old_dict_messages else None)

        generator.send(message.as_dict())
        for text_snippet in generator.generate():
            print("text_snippet", text_snippet)
            yield text_snippet

    print("generator.messages", generator.messages)
    # 切片获取发送后新增的几条消息
    new_messages = generator.messages[len(old_dict_messages):]
    print("new_messages", new_messages)
    # 向数据库中新增消息
    for message in new_messages:
        db_session.add(Message(
            role=message.get("role"),
            content=message.get("content"),
            tag=message.get("tag"),
            user=user))
    print("commit")
    db_session.commit()

@generator_bp.route('/send', methods=['POST'])
def generator_send():
    message = Message(
        role="user",
        content=request.data.decode(),
        tag=request.args.get('tag'),
        user=g.user
    )

    if len(executor._threads) >= executor._max_workers:
        return res(current_app, {
            "code": 500,
            "msg": "Server is busy."
        });
    for thread in executor._threads:
        print("name", thread.getName())
        if thread.getName() == g.user_id:
            return res(current_app, {
                "code": -1,
                "msg": "Once a time."
            });
    bgtask = executor.submit(thinking_bgtask, message, g.user)
    bgtask.name = g.user_id
    
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
