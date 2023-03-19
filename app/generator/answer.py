import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def choiceQues(ques):
    text = "{num}. {text}\n".format_map(ques)
    for option in ques["options"]:
        text += "{choice}. {text}\n".format_map(option)
    return text

class AnswersGenerator():
    def __init__(self, messages=[]):
        self.messages = messages
    
    def send(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
    
    def generate(self):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            stream=True,
            messages=self.messages)
        
        print(completion)
        text = ""
        for event in completion:
            text_snippet = event.choices[0]['delta'].get('content', '')
            text += text_snippet
            yield text_snippet
        self.messages.append({"role": "assistant", "content": text})
    
    @staticmethod
    def generatePrompt(document):
        prompt = """目的：生成以下题目的答案
要求：
1. 除了答案不得生成任何其它东西，除非我要求你解释答案
2. 如有文章，参考文章进行答题
2. 每题的答案都要标出题号
3. 选择题不要重复选项内容，只需填的序号

"""
        # for block in document:
            # if block["type"] == "choice_ques":
                # prompt += choiceQues(block) + '\n'
        # # 切片清除最后一个换号
        # return prompt[:-1]
        prompt += document
        return prompt
    