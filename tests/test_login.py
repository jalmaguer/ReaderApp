def test_login(client, auth):
    assert client.get('/login').status_code == 200
    response = auth.login()
    assert response.headers['Location'] == 'http://localhost/'

def test_login_logout(auth):
    auth.login()
    auth.logout()