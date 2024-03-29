import os, time


def choiceQues(ques):
    text = "{num}. {text}\n".format_map(ques)
    for option in ques["options"]:
        text += "{choice}. {text}\n".format_map(option)
    return text

class AnswersGenerator():
    def __init__(self, messages=None):
        if messages is None: messages = [{
          "role": "system",
          "content": """目的：生成以下题目的答案
要求：
除了答案不得生成任何其它东西
每题的答案都要标出题号
选择题不要重复选项内容，只需填的序号
不是题目，无法回答请说明。回答尽量简短准确"""}]
        self.messages = messages
        # 只保留API能接受的属性
        self.apiMessages = [{k: v for k, v in msg.items() if k in ['role', 'content']} for msg in messages]
    
    def send(self, message):
        self.messages.append(message)
        self.apiMessages.append({
          "role": message.get("role"),
          "content": message.get("content")
        })
    
    def generate(self):
        print(self.apiMessages)
        def completion():
            for i in range(10):
                yield {"choices": [{"delta": {"content": str(i)}}]}
                time.sleep(0.5)
        
        text = ""
        for event in completion():
            text_snippet = event['choices'][0]['delta'].get('content', '')
            text += text_snippet
            yield text_snippet
        self.messages.append({"role": "assistant", "content": text})
    
    @staticmethod
    def generatePrompt(document):
        prompt = ""
        # for block in document:
            # if block["type"] == "choice_ques":
                # prompt += choiceQues(block) + '\n'
        # # 切片清除最后一个换号
        # return prompt[:-1]
        prompt += document
        return prompt
    
