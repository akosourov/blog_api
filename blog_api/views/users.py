from blog_api.models import db, User
from blog_api.helpers import (error_response, success_response,
                              HTTP_400_BAD_REQUEST, HTTP_201_CREATED)
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError


users = Blueprint('users', __name__)


@users.route('/v1/users', methods=['POST'])
def create_user():
    user = request.get_json(force=True)
    username = user.get('username')
    if not username:
        return error_response(HTTP_400_BAD_REQUEST, '`username` is required')
    user = User(username=username)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        return error_response(HTTP_400_BAD_REQUEST, 'User already exists')

    return success_response(HTTP_201_CREATED, {'username': username})
