import os, json
from collections import UserDict


def res(app, data):
    #mdict["code"] = mdict.get("code", 0)
    json = {}
    if isinstance(data, dict):
        json['code'] = data.pop("code", 0)
        if "message" in data: json['message'] = data.pop("message")
    else:
        json['code'] = 0
    if data:
        json['data'] = data

    res = app.json.response(json)
    if json['code'] < 0: res.status = 400
    return res

class Users(UserDict):
    def __init__(self, json_path):
        self.json_file = open(json_path, "r+")
        # 读取首字节来查看文件是否是不是空的
        if not self.json_file.read(1):
            self.json_file.write("{}")
        self.json_file.seek(0)
        self.data = json.load(self.json_file)
        self.json_file.seek(0)
    def save(self):
        json.dump(self.data, self.json_file)
        self.json_file.seek(0)
