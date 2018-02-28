import unittest
from reader_app import app
from create_database import create_data_base


class TestApp(unittest.TestCase):

    def setUp(self):
        create_data_base('test.db')
        app.config['DATABASE'] = 'test.db'
        self.app = app.test_client()

    def tearDown(self):
        pass

    def login(self, username, password):
        return self.app.post('/login', data=dict(username=username, pw=password), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('admin', 'admin')
        rv = self.logout()

    def test_add_language(self):
        self.login('admin', 'admin')
        rv = self.app.post('/add_language', data=dict(language='French'), follow_redirects=True)
        assert b'French' in rv.data

if __name__ == '__main__':
    unittest.main()