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

def parse_body(req, default):
    # 根据请求的内容类型解析 body
    content_type = req.headers.get("Content-Type")
    if content_type == "application/json":
        data = req.get_json(silent=True) 
    elif content_type == "multipart/form-data":
        data = req.form.to_dict()
    else:
        data = req.get_json(force=True, silent=True)

    return data if data is not None else default

class Users(UserDict):
    def __init__(self, json_path):
        self.json_path = json_path
        with open(self.json_path, "r") as json_file:
            self.data = json.load(json_file)
    def save(self):
        with open(self.json_path, "w") as json_file:
            json.dump(self.data, json_file)
