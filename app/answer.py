import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def choiceQues(ques):
    text = "{num}. {text}\n".format_map(ques)
    for option in ques["options"]:
        text += "{choice}. {text}\n".format_map(option)
    return text

class AnswersGenerater():
    def __init__(self, messages=[]):
        self.messages = messages
    
    def send(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
    
    def generate(self):
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
            messages=self.messages)
        self.messages.append(completion.choices[0].message)
        return self.messages[-1]
    
    @staticmethod
    def generatePrompt(document):
        prompt = """目的：生成以下题目的答案
要求：
1. 每题的答案都要标出题号
2. 选择题不要重复选项内容，只需选项答案
3. 除了答案不要生成任何其它东西，除非我要求你解释答案
4. 勇于承认自己的错误，不要为错误解释

"""
        for block in document:
            if block["type"] == "choice_ques":
                prompt += choiceQues(block) + '\n'
        # 切片清除最后一个换号
        return prompt[:-1]
    