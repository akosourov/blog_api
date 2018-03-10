from flask import jsonify


HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404


def error_response(status_code, msg):
    resp = jsonify({'error': msg})
    resp.status_code = status_code
    return resp


def success_response(status_code, data=None):
    resp = jsonify(data or {})
    resp.status_code = status_code
    return resp
