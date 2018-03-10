from blog_api.models import db, User
from blog_api.helpers import (error_response, success_response,
                              HTTP_400_BAD_REQUEST, HTTP_201_CREATED,
                              contains_only_letters_and_numbers)
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError


users_bp = Blueprint('users', __name__)


def parse_validate_user_raw(raw):
    if not raw:
        return None, 'Field `username` is required'
    username = raw.get('username')
    if not username:
        return None, 'Field `username` is required'
    if not contains_only_letters_and_numbers(username):
        return None, 'Bad field `username`'
    user_cleaned = {
        'username': username
    }
    return user_cleaned, None


@users_bp.route('/v1/users', methods=['POST'])
def create_user():
    user_raw = request.get_json(force=True)
    user_cleaned, error = parse_validate_user_raw(user_raw)
    if error:
        return error_response(HTTP_400_BAD_REQUEST, error)
    user = User(username=user_cleaned['username'])
    db.session.add(user)
    try:
        db.session.commit()
        db.session.flush()
    except IntegrityError:
        return error_response(HTTP_400_BAD_REQUEST, 'User already exists')

    return success_response(HTTP_201_CREATED, {'id': user.id,
                                               'username': user.username})
