import os

import pytest

from app import app, init_db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_database.db'
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
        if os.path.exists('test_database.db'):
            os.remove('test_database.db')


def test_login_page_get(client):
    response = client.get('/')
    assert response.status_code == 200


def test_login_post_valid(client):
    response = client.post(
        '/',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_login_post_invalid(client):
    response = client.post(
        '/',
        data={'username': 'wrong', 'password': 'wrong'},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_status_route(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.json == {"status": "running"}


def test_dashboard_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200


def test_dashboard_after_login(client):
    client.post('/', data={'username': 'admin', 'password': '1234'})
    response = client.get('/dashboard')
    assert response.status_code == 200


def test_logout(client):
    client.post('/', data={'username': 'admin', 'password': '1234'})
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


def test_add_device_authenticated(client):
    client.post('/', data={'username': 'admin', 'password': '1234'})
    response = client.post(
        '/add',
        data={
            'name': 'Test',
            'ip': '1.1.1.1',
            'port': '80',
            'type': 'Routeur'
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_add_device_without_login(client):
    response = client.post(
        '/add',
        data={'name': 'Test'},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_add_page_access_authenticated(client):
    client.post('/', data={'username': 'admin', 'password': '1234'})
    response = client.get('/add')
    assert response.status_code == 200


def test_add_page_access_without_login(client):
    response = client.get('/add', follow_redirects=True)
    assert response.status_code == 200


def test_404_page(client):
    response = client.get('/route_inexistante')
    assert response.status_code == 404


def test_session_persistence(client):
    client.post('/', data={'username': 'admin', 'password': '1234'})
    assert client.get('/dashboard').status_code == 200
    assert client.get('/add').status_code == 200
    assert client.get('/dashboard').status_code == 200
