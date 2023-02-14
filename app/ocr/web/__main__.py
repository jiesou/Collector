import json
from flask import Flask
import units.response

app = Flask(__name__,
    static_url_path='ui', 
    static_folder='ui')

@app.errorhandler(HTTPException)
def http_error(e):
    res = e.get_response()
    res.data = response({
        "code": e.code,
        "message": e.name})
    res.content_type = "application/json"
    return response

@app.route("/")
def index():
    return response({
        "status": "running",
        "version": "1.0.0"})

