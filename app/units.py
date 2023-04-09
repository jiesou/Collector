from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
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


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    imgs = db.relationship('Img', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

class Img(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String)
    document_text = db.Column(db.String)
    document_status = db.Column(db.String)
 
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String)
    content = db.Column(db.String)
    tag = db.Column(db.String)
