import json
import unittest
from blog_api.app import create_json_app
from blog_api.models import db


test_settings = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///test_blog.db'
}


class Base(unittest.TestCase):
    def setUp(self):
        self.app = create_json_app(test_settings)
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        db.drop_all(app=self.app)


class JsonErrorsTest(Base):
    def test_404_json_error_if_not_found(self):
        resp = self.client.get('/smth')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

    def test_405_json_error_if_method_not_allowed(self):
        resp = self.client.get('/v1/users')
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')


class UsersTest(Base):
    def test_create_user(self):
        resp = self.client.post('/v1/users',
                                data=json.dumps({'username': 'Petya'}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)

        # Already exists
        resp = self.client.post('/v1/users',
                                data=json.dumps({'username': 'Petya'}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post('/v1/users',
                                data=json.dumps({'username': 'Vasya'}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)


if __name__ == '__main__':
    unittest.main()
