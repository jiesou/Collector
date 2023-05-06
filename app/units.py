from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from celery import Celery, Task
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

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery
    return celery

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

class User(BaseModel):
    id = db.Column(db.String, primary_key=True)
    imgs = db.relationship('Img', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

class Img(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String)
    document_text = db.Column(db.String)
    document_status = db.Column(db.String)

class Message(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String)
    content = db.Column(db.String)
    tag = db.Column(db.String)

