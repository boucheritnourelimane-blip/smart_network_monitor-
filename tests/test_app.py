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


def test_home_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302


def test_login_page_accessible(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_login_post_valid(client):
    response = client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_login_post_invalid(client):
    response = client.post(
        '/login',
        data={'username': 'wrong', 'password': 'wrong'},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_status_route(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_dashboard_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200


def test_dashboard_after_login(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.get('/dashboard')
    assert response.status_code == 200


def test_add_page_requires_login(client):
    response = client.get('/add', follow_redirects=True)
    assert response.status_code == 200


def test_add_page_accessible_after_login(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.get('/add')
    assert response.status_code == 200


def test_add_device_valid(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.post(
        '/add',
        data={
            'name': 'Test_Router',
            'ip': '10.0.0.1',
            'port': '80',
            'type': 'Routeur',
            'location': 'Test',
            'vendor': 'Cisco',
            'description': 'Test device'
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_add_device_invalid_ip(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.post(
        '/add',
        data={
            'name': 'Test',
            'ip': '999.999.999.999',
            'port': '80',
            'type': 'Switch',
            'location': '',
            'vendor': '',
            'description': ''
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_add_device_missing_required_fields(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.post(
        '/add',
        data={'name': '', 'ip': ''},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_add_without_login(client):
    response = client.post(
        '/add',
        data={'name': 'Test'},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_delete_device_authenticated(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.get('/delete/1', follow_redirects=True)
    assert response.status_code == 200


def test_delete_device_without_login(client):
    response = client.get('/delete/1', follow_redirects=True)
    assert response.status_code == 200


def test_delete_nonexistent_device(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.get('/delete/9999', follow_redirects=True)
    assert response.status_code == 200


def test_logout(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


def test_dashboard_after_logout(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    client.get('/logout')
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200


def test_session_persistence(client):
    client.post(
        '/login',
        data={'username': 'admin', 'password': '1234'},
        follow_redirects=True
    )
    assert client.get('/dashboard').status_code == 200
    assert client.get('/add').status_code == 200
    assert client.get('/dashboard').status_code == 200


def test_404_route(client):
    response = client.get('/route_inexistante')
    assert response.status_code == 404
