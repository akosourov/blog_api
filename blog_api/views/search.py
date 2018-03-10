from blog_api.models import db
from blog_api.helpers import (error_response, success_response,
                              HTTP_400_BAD_REQUEST,
                              HTTP_200_OK, contains_only_letters_and_numbers)
from flask import Blueprint, request
from sqlalchemy.sql import text


search_bp = Blueprint('search', __name__)


@search_bp.route('/v1/search')
def search():
    tags_arg = request.args.get('tags')
    if tags_arg:
        tags_name = tags_arg.split(',')
        for tag in tags_name:
            if not contains_only_letters_and_numbers(tag):
                return error_response(HTTP_400_BAD_REQUEST, 'Bad param `tags`')
    else:
        tags_name = []

    date_beg_arg = request.args.get('date_begin')
    date_end_arg = request.args.get('date_end')
    title_arg = request.args.get('title')
    if not tags_arg and not date_beg_arg and not date_end_arg and not title_arg:
        return success_response(HTTP_200_OK, [])

    if not tags_arg:
        sql_search_template = """
            SELECT p.id, p.title, p.body, p.pub_date
            FROM post p
            WHERE
              {search_date_begin}
              AND {search_date_end}
              AND {search_title}
            
        """
        sql_search = sql_search_template.format(
            search_date_begin='p.pub_date >= :date_begin' if date_beg_arg else 1,
            search_date_end='p.pub_date <= :date_end' if date_end_arg else 1,
            search_title='p.title LIKE :title' if title_arg else 1
        )
    else:
        # Поиск в том числе по тегам
        sql_search_template = """
            WITH cte_tags as (
              select t.id
              from tag t
              where t.name IN ({search_tags})
            )
            SELECT DISTINCT p.id, p.title, p.body, p.pub_date
              FROM post p
                join tag_post tp ON p.id = tp.post_id
                join cte_tags c ON tp.tag_id = c.id
              WHERE
                {search_date_begin}
                AND {search_date_end}
                AND {search_title}

        """
        sql_search = sql_search_template.format(
            search_tags=str(tags_name)[1:-1],
            search_date_begin='p.pub_date >= :date_begin' if date_beg_arg else 1,
            search_date_end='p.pub_date <= :date_end' if date_end_arg else 1,
            search_title='p.title LIKE :title' if title_arg else 1
        )
    stmt = text(sql_search)
    conn = db.engine.connect()
    args = {}
    if title_arg:
        args['title'] = '%' + title_arg + '%'
    if date_beg_arg:
        args['date_begin'] = date_beg_arg
    if date_end_arg:
        args['date_end'] = date_end_arg
    cursor = conn.execute(stmt, **args)
    res = []
    for rec in cursor:
        post_id, post_title, post_body, post_pub_date = rec
        res.append({
            'id': post_id,
            'title': post_title,
            'body': post_body,
            'pub_date': post_pub_date
        })
    return success_response(HTTP_200_OK, res)
