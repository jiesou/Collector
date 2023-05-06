from flask import Flask, send_from_directory, stream_with_context, request, g
from sqlalchemy.orm import sessionmaker
from lib.flask_sqlalchemy_session import flask_scoped_session
from werkzeug.exceptions import HTTPException
import os
from units import res, celery_init_app, db, User
from imgs import imgs_bp
from generator import generator_bp

app = Flask(__name__)

app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
app.config.from_mapping(
    MAX_CONTENT_LENGTH = 1024 * 1024 * 30,
    UPLOAD_FOLDER = os.path.join(app.config['DATA_FOLDER'], 'user-upload'),

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + \
        os.path.join(app.config['DATA_FOLDER'], "users.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    
    CELERY=dict(
        broker_url="redis://localhost",
        result_backend="redis://localhost",
       # task_ignore_result=True,
    ),
)
app.config.from_prefixed_env()

celery_init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()
app.register_blueprint(imgs_bp, url_prefix='/api/imgs')
app.register_blueprint(generator_bp, url_prefix='/api/generator')


@app.errorhandler(HTTPException)
def http_error(e):
    response = res(app, {
        'code': e.code,
        'message': e.name})
    response.status = e.code
    return response

@app.before_request
def authentication():
    if not request.path.startswith("/api/"): return None
    if "User-Id" in request.headers:
        g.user_id = request.headers['User-Id']
        
        g.user = db.session.query(User).get(g.user_id)
        if g.user is None:
            g.user = User(id=g.user_id)
            db.session.add(g.user)
    else:
        return res(app, {
            "code": -1,
            "message": "Authentication failed"
        })

@app.after_request
def save_users(response):
    if request.path.startswith("/api/"):
        db.session.commit()
    return response

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/<path:file>')
def static_ui(file):
    return send_from_directory('ui', file)

@app.route('/user-upload/<path:file>')
def user_upload(file):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file)

@app.route('/api')
def api_index():
    return res(app, {
        'status': 'running',
        'version': '1.0.0'})

if __name__ == '__main__':
    app.run(port=3000, use_reloader=True)
