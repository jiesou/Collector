from flask import Flask, send_from_directory, stream_with_context, request, g
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import HTTPException
import os
from units import res, User, db
from imgs import imgs_bp
from generator import generator_bp

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 30
# 最大上传大小 30M
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['DATA_FOLDER'], 'user-upload')

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + \
    os.path.join(app.config['DATA_FOLDER'], "users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()
    app.db_session_factory = sessionmaker(bind=db.engine)
    db_session = scoped_session(app.db_session_factory)
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
        g.db_session = db_session
        g.user_id = request.headers['User-Id']
        
        g.user = g.db_session.query(User).get(g.user_id)
        if g.user is None:
            g.user = User(id=g.user_id)
            g.db_session.add(g.user)
    else:
        return res(app, {
            "code": -1,
            "message": "Authentication failed"
        })

@app.after_request
def save_users(response):
    if request.path.startswith("/api/"):
        g.db_session.commit()
    return response

@app.teardown_appcontext
def shutdown_session(exception=None):
    if hasattr(g, 'db_session'):
        g.db_session.remove()

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
