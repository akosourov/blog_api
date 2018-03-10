from blog_api.models import db, Post, User, Tag
from blog_api.helpers import (error_response, success_response,
                              HTTP_400_BAD_REQUEST, HTTP_201_CREATED,
                              HTTP_200_OK, HTTP_404_NOT_FOUND,
                              contains_only_letters_and_numbers)
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError


posts_bp = Blueprint('posts', __name__)


def parse_validate_post(post_raw):
    if not post_raw:
        return None, 'Body is empty'

    title = post_raw.get('title')
    body = post_raw.get('body')
    if not title or not body:
        return None, 'Fields `title` and `body` are required'

    tags = post_raw.get('tags') or []
    if not isinstance(tags, list):
        return None, 'Field `tags` is invalid'
    if len(tags) > 10:
        return None, 'Field `tags` is invalid. Max length is 10'
    for tag_name in tags:
        if not tag_name or not contains_only_letters_and_numbers(tag_name):
            return None, 'Field `tags` is invalid'

    post_cleaned = {
        'title': title,
        'body': body,
        'tags': tags
    }
    return post_cleaned, None


@posts_bp.route('/v1/users/<int:user_id>/posts', methods=['GET', 'POST'])
def get_user_post_or_create(user_id):
    if request.method == 'GET':
        return get_user_posts(user_id)
    else:
        return create_post(user_id)


def get_user_posts(user_id):
    query = Post.query.filter(Post.user_id == user_id)
    sort_arg = request.args.get('sort')
    if sort_arg == 'pub_date':
        query = query.order_by(Post.pub_date)
    elif sort_arg == '-pub_date':
        query = query.order_by(Post.pub_date.desc())
    posts_res = [
        {
            'id': post.id,
            'title': post.title,
            'body': post.body,
            'pub_date': post.pub_date,
            'tags': [t.name for t in post.tags],
        }
        for post in query.all()
    ]
    return success_response(HTTP_200_OK, posts_res)


def create_post(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(HTTP_404_NOT_FOUND, 'User does not exist')

    post_raw = request.get_json(force=True)
    post_cleaned, error = parse_validate_post(post_raw)
    if error:
        return error_response(HTTP_400_BAD_REQUEST, error)

    tags = []
    tags_name = post_cleaned['tags']
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
    post = Post(title=post_cleaned['title'], body=post_cleaned['body'],
                user_id=user_id, tags=tags)
    db.session.add(post)
    try:
        db.session.commit()
        db.session.flush()
    except IntegrityError:
        return error_response(HTTP_400_BAD_REQUEST, 'Could not create post')

    return success_response(HTTP_201_CREATED, {'id': post.id,
                                               'pub_date': post.pub_date,
                                               'title': post.title,
                                               'tags': [t.name
                                                        for t in post.tags]})
