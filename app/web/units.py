import json
from flask import Flask
def response(app, mdict):
    #mdict["code"] = mdict.get("code", 0)
    mdict.setdefault("code", 0)
    return app.json.response(mdict)