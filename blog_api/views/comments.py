from blog_api.models import db, Comment, Post, User
from blog_api.helpers import (error_response, success_response,
                              HTTP_400_BAD_REQUEST, HTTP_201_CREATED,
                              HTTP_200_OK, HTTP_404_NOT_FOUND,
                              HTTP_403_FORBIDDEN)
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError


comments_bp = Blueprint('comments', __name__)


def parse_validate_comment_raw(raw):
    if not raw:
        return None, 'Body is empty'
    body = raw.get('body')
    if not body:
        return None, 'Field `body` is required'
    body = str(body)
    # todo escape html tags
    if len(body) > 10000:
        return None, 'Field `body` is too long. Max length is 10000'
    user_id = raw.get('user_id')
    if not user_id:
        return None, 'Field `user_id` is required'
    try:
        user_id = int(user_id)
    except ValueError:
        return None, 'Bad field `user_id`'
    comment_cleaned = {'body': body, 'user_id': user_id}
    return comment_cleaned, None


@comments_bp.route('/v1/users/<int:user_id>/posts/<int:post_id>/comments',
                   methods=['GET', 'POST'])
def get_comments_or_create(user_id, post_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(HTTP_404_NOT_FOUND, 'User does not exist')
    post = Post.query.get(post_id)
    if not post:
        return error_response(HTTP_404_NOT_FOUND, 'Post does not exist')

    if request.method == 'GET':
        return get_comments(post_id)
    else:
        return create_comment(post_id)


def get_comments(post_id):
    query = Comment.query.filter(Comment.post_id == post_id)
    sort_arg = request.args.get('sort')
    if sort_arg == 'pub_date':
        query = query.order_by(Comment.pub_date)
    elif sort_arg == '-pub_date':
        query = query.order_by(Comment.pub_date.desc())
    comments = [
        {
            'id': comment.id,
            'body': comment.body,
            'pub_date': comment.pub_date,
        }
        for comment in query.all()
    ]
    return success_response(HTTP_200_OK, comments)


def create_comment(post_id):
    comment_raw = request.get_json(force=True)
    comment_cleaned, error = parse_validate_comment_raw(comment_raw)
    if error:
        return error_response(HTTP_400_BAD_REQUEST, error)

    for_user_id = comment_cleaned['user_id']
    post = Post.query.get(post_id)
    if not post:
        return error_response(HTTP_404_NOT_FOUND, 'Post does not exist')
    for ban in post.banned_users:
        if ban.user_id == for_user_id:
            return error_response(HTTP_403_FORBIDDEN, 'This user is not allowed to create comments')

    comment = Comment(body=comment_cleaned['body'], user_id=for_user_id, post_id=post_id)
    db.session.add(comment)
    try:
        db.session.commit()
        db.session.flush()
    except IntegrityError:
        return error_response(HTTP_400_BAD_REQUEST, 'Post does not belong this user')
    return success_response(HTTP_201_CREATED, {'id': comment.id,
                                               'pub_date': comment.pub_date})
