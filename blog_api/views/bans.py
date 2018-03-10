from blog_api.models import db, Post, User, BanForComment
from blog_api.helpers import (error_response, success_response,
                              HTTP_400_BAD_REQUEST, HTTP_201_CREATED,
                              HTTP_200_OK, HTTP_404_NOT_FOUND)
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError


bans_bp = Blueprint('bans', __name__)


def parse_validate_ban_raw(raw):
    if not raw:
        return None, 'Field `user_id` is required'
    user_id = raw.get('user_id')
    if not user_id:
        return None, 'Field `user_id` is required'
    try:
        user_id = int(user_id)
    except ValueError:
        return None, 'Bad field `user_id`'

    return {'user_id': user_id}, None


@bans_bp.route('/v1/users/<int:user_id>/posts/<int:post_id>/bans',
               methods=['POST'])
def create_ban(user_id, post_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(HTTP_404_NOT_FOUND, 'User does not exist')
    post = Post.query.get(post_id)
    if not post:
        return error_response(HTTP_404_NOT_FOUND, 'Post does not exist')

    ban_raw = request.get_json(force=True)
    ban_cleaned, error = parse_validate_ban_raw(ban_raw)
    if error:
        return error_response(HTTP_400_BAD_REQUEST, error)

    for_user_id = ban_cleaned['user_id']
    for_user = User.query.get(for_user_id)
    if not for_user:
        return error_response(HTTP_404_NOT_FOUND, 'User does not exist')
    ban = BanForComment.query.filter(
        BanForComment.post_id == post_id,
        BanForComment.user_id == for_user_id
    ).first()
    if ban:
        return error_response(HTTP_400_BAD_REQUEST, 'Ban for this user and post already exists')
    else:
        ban = BanForComment(post_id=post_id, user_id=for_user_id)
        db.session.add(ban)
        try:
            db.session.commit()
            db.session.flush()
        except IntegrityError:
            return error_response(HTTP_400_BAD_REQUEST, 'Post or user does not exist')

    return success_response(HTTP_201_CREATED, {'id': ban.id,
                                               'user_id': ban.user_id,
                                               'post_id': ban.post_id})


@bans_bp.route('/v1/users/<int:user_id>/posts/<int:post_id>/bans/<int:ban_id>',
               methods=['DELETE'])
def delete_ban(user_id, post_id, ban_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(HTTP_404_NOT_FOUND, 'User does not exist')
    post = Post.query.get(post_id)
    if not post:
        return error_response(HTTP_404_NOT_FOUND, 'Post does not exist')
    ban = BanForComment.query.get(ban_id)
    if not ban:
        return error_response(HTTP_404_NOT_FOUND, 'Ban does not exist')
    else:
        db.session.delete(ban)
        try:
            db.session.commit()
        except IntegrityError:
            return error_response(HTTP_400_BAD_REQUEST, 'Already deleted')

    return success_response(HTTP_200_OK)
