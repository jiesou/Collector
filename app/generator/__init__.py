from flask import Blueprint, current_app, stream_with_context, request, g
import threading
from units import res, parse_body
from .answer import AnswersGenerator

generator_bp = Blueprint('Generator', __name__)

@generator_bp.route('/api/generate_prompt', methods=['POST'])
def generate_prompt():
    body = parse_body(request)
    body.setdefault("imgs", g.user["imgs"])
    # 未指定需要处理的页数就遍历全部图片
    body.setdefault("indexs", range(len(body["imgs"])))
    document = []
    for index in body["indexs"]:
        img = body["imgs"][index]
        document += img.get("document")
    
    prompt = AnswersGenerator.generatePrompt(document)
    return res(current_app, {'prompt': prompt})


def GeneratorAnswer(queue, user, prompt):
    generator = AnswersGenerator(user['messages'])
    generator.send(prompt)
    last_message = generator.generate()
    # 更新 用户数据 中的 消息列表
    user['messages'] = generator.messages
    user['messages_status'] = "waiting"
    queue.put(last_message)

@generator_bp.route('/api/generator/send', methods=['POST'])
def generator_send():
    def stream():
        queue = threading.Queue()
        generator_thread = threading.Thread(target=GeneratorAnswer,
          args=(queue, g.user, request.data.decode()),
          daemon=True)
        generator_thread.start()
        g.user["messages_status"] = "thinking"
        
        while True:
            last_message = queue.get()
            if last_message is None: break
            return last_message
    return res(current_app, stream_with_context(stream()))

@generator_bp.route('/api/generator/messages')
def generator_messages():
    return res(current_app, g.user["messages"])

@generator_bp.route('/api/generator/clear')
def generator_clean():
    g.user["messages"] = []
    return res(current_app, {'message': 'ok'})
