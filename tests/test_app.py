import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_status(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.json == {"status": "running"}

def test_dashboard_no_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200

def test_logout(client):
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200