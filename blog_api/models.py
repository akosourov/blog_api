from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


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