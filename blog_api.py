from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, default_exceptions


def make_json_app(app_name):
    app = Flask(app_name)

    def default_json_error(exc):
        resp = jsonify({'message': str(exc)})
        resp.status_code = (exc.code
                            if isinstance(exc, HTTPException) else 500)
        return resp

    for code in default_exceptions:
        app.register_error_handler(code, default_json_error)

    return app


app = make_json_app(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)


tag_post_table = db.Table(
    'tag_post',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<User: %s>' % self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    tags = db.relationship('Tag', secondary=tag_post_table,
                           backref=db.backref('posts'))

    def __repr__(self):
        return '<Post: %s>' % self.title


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return '<Comment :%s>' % self.body[:10]


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<Tag :%s>' % self.name[:10]


def init_db():
    db.create_all()


def drop_db():
    db.drop_all()


def error_response(status_code, msg):
    resp = jsonify({'message': msg})
    resp.status_code = status_code
    return resp


def success_response(status_code, data=None):
    resp = jsonify(data or {})
    resp.status_code = status_code
    return resp


@app.route('/')
def index():
    api_scheme = ['/users/', '/posts/', '/search/']
    return jsonify(api_scheme)


@app.route('/v1/users/', methods=['POST'])
def create_user():
    user = request.get_json(force=True)
    username = user.get('username')
    if not username:
        return error_response(400, 'username is required')
    user = User(username=username)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        return error_response(400, 'User already exists')
    resp = jsonify({'username': username})
    resp.status_code = 201
    return resp


@app.route('/v1/users/<int:user_id>/')
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(404, 'User not found')
    return jsonify(username=user.username)


@app.route('/v1/posts/', methods=['POST'])
def create_post():
    post_raw = request.get_json(force=True)
    if post_raw is None:
        return error_response(400, 'Bad json body')
    user_id, tags_name, title, body = post_raw.get('user_id'), post_raw.get('tags'), post_raw.get('title'), post_raw.get('body')
    if not user_id or not title or not body:
        return error_response(400, '`user_id`, `title`, `body` are required')
    try:
        user_id = int(user_id)
    except ValueError:
        return error_response(400, 'bad `user_id`')
    print('user_id', user_id)
    if not User.query.get(user_id):
        return error_response(400, 'User with user_id=%s does not exist')

    tags = []
    if isinstance(tags_name, list):
        if len(tags_name) > 10:
            return error_response(400, 'tags list too long. Max length is 10')
        for name in tags_name:
            tag = Tag.query.filter(Tag.name == name).first()
            if not tag:
                # create tag
                db.session.add(Tag(name=name))
                try:
                    db.session.commit()
                except IntegrityError:
                    # tag already exists
                    db.session.rollback()
                finally:
                    tag = Tag.query.filter(Tag.name == name).first()
            if tag:
                tags.append(tag)
    post = Post(title=title, body=body, user_id=user_id, tags=tags)
    db.session.add(post)
    try:
        db.session.commit()
    except IntegrityError:
        return error_response(400, 'Could not create post')
    resp = jsonify()
    resp.status_code = 201
    return resp


@app.route('/v1/users/<int:user_id>/posts/')
def get_user_posts(user_id):
    posts_query = Post.query.filter(Post.user_id == user_id)
    if request.args.get('order') == 'desc':
        posts_query = posts_query.order_by(Post.pub_date.desc())
    else:
        posts_query = posts_query.order_by(Post.pub_date)
    posts_res = [
        {
            'id': post.id,
            'title': post.title,
            'body': post.body,
            'pub_date': post.pub_date,
            'tags': [],
        }
        for post in posts_query.all()
    ]
    return jsonify(posts_res)


def get_comments(post_id):
    query = Comment.query.filter(Comment.post_id == post_id)
    if request.args.get('order') == 'desc':
        query = query.order_by(Comment.pub_date.desc())
    else:
        query = query.order_by(Comment.pub_date)
    comments = [
        {
            'id': comment.id,
            'body': comment.body,
            'pub_date': comment.pub_date,
        }
        for comment in query.all()
    ]
    return jsonify(comments)


def create_comment(post_id):
    comment_raw = request.get_json(force=True)
    # Validation
    if not comment_raw:
        return error_response(400, 'Bad json body')
    user_id, body = comment_raw.get('user_id'), comment_raw.get('body')
    if not user_id or not body:
        return error_response(400, '`user_id` and `body` are required')
    try:
        user_id = int(user_id)
    except ValueError:
        return error_response(400, 'bad `user_id`')

    # todo escape body_text
    body = str(body)

    comment = Comment(body=body, user_id=user_id, post_id=post_id)
    db.session.add(comment)
    try:
        db.session.commit()
    except IntegrityError:
        return error_response(400, 'user or post does not exist')
    return success_response(201)


@app.route('/v1/posts/<int:post_id>/comments/', methods=['GET', 'POST'])
def get_or_create_comments(post_id):
    post = Post.query.get(post_id)
    if not post:
        return error_response(404, 'Post does not exist')

    if request.method == 'GET':
        return get_comments(post_id)
    else:
        return create_comment(post_id)


if __name__ == '__main__':
    app.run()
