from flask import Flask
from werkzeug.exceptions import HTTPException
from units import response

app = Flask(__name__,
    static_url_path='/ui', 
    static_folder='ui')

@app.route("/")
def index():
    return response({
        "status": "running",
        "version": "1.0.0"})

@app.errorhandler(HTTPException)
def http_error(e):
    res = e.get_response()
    res.data = response({
        "code": e.code,
        "message": e.name})
    res.content_type = "application/json"
    return response

