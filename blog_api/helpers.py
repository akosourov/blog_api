from flask import jsonify
import re


HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404

only_letters_and_numbers_pattern = re.compile(r'^[A-Za-z0-9]*$')


def error_response(status_code, msg):
    resp = jsonify({'error': msg})
    resp.status_code = status_code
    return resp


def success_response(status_code, data=None):
    resp = jsonify(data or {})
    resp.status_code = status_code
    return resp


def contains_only_letters_and_numbers(string):
    m = only_letters_and_numbers_pattern.match(string)
    return m is not None
