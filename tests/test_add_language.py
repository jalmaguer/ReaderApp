def test_add_language(client, auth):
    auth.login()
    rv = client.post('/add_language', data=dict(language='French'), follow_redirects=True)
    auth.logout()
    assert b'French' in rv.data
