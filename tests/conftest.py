import pytest
from reader_app import app
from create_database import create_data_base


@pytest.fixture
def app_fixture():
    create_data_base('test.db')
    app.config['DATABASE'] = 'test.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    return app

@pytest.fixture
def client(app_fixture):
    return app_fixture.test_client()

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='admin', pw='admin'):
        return self._client.post(
            '/login',
            data={'username': username, 'pw': pw}
        )

    def logout(self):
        return self._client.get('/logout')

@pytest.fixture
def auth(client):
    return AuthActions(client)