import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ── Test login page ──
def test_login_page(client):
    response = client.get('/')
    assert response.status_code == 200

# ── Test login correct ──
def test_login_success(client):
    response = client.post('/', data={
        'username': 'admin',
        'password': '1234'
    }, follow_redirects=True)
    assert response.status_code == 200

# ── Test login incorrect ──
def test_login_wrong(client):
    response = client.post('/', data={
        'username': 'wrong',
        'password': 'wrong'
    }, follow_redirects=True)
    assert b'incorrect' in response.data

# ── Test dashboard sans login ──
def test_dashboard_no_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200

# ── Test status API ──
def test_status(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.json == {"status": "running"}

# ── Test add sans login ──
def test_add_no_login(client):
    response = client.get('/add', follow_redirects=True)
    assert response.status_code == 200

# ── Test logout ──
def test_logout(client):
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200