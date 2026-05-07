"""
Fichier de tests unitaires pour Smart Network Monitor
Adapté à l'application avec authentification admin/1234
"""

import pytest
import sqlite3
import os
from app import app, init_db


@pytest.fixture
def client():
    """
    Fixture qui fournit un client de test Flask
    Simule un navigateur pour tester les routes HTTP
    """
    # Configuration pour les tests
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Utiliser une base de données temporaire pour les tests
    app.config['DATABASE'] = 'test_database.db'
    
    with app.test_client() as client:
        with app.app_context():
            # Recréer la base de données de test
            init_db()
        yield client
        
        # Nettoyer après les tests
        if os.path.exists('test_database.db'):
            os.remove('test_database.db')


def test_login_page_get(client):
    """Test 1: Vérifier que la page de login s'affiche correctement"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'username' in response.data.lower() or b'password' in response.data.lower()


def test_login_post_valid(client):
    """Test 2: Vérifier la connexion avec identifiants valides (admin/1234)"""
    response = client.post('/', data={
        'username': 'admin',
        'password': '1234'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert len(response.history) > 0
    assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()


def test_login_post_invalid(client):
    """Test 3: Vérifier que les identifiants invalides sont rejetés"""
    response = client.post('/', data={
        'username': 'wrong_user',
        'password': 'wrong_pass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Vérifie qu'on est toujours sur la page login
    assert b'login' in response.data.lower() or b'connexion' in response.data.lower()
    # Vérifie que le dashboard n'est PAS accessible (pas de redirection)
    assert b'dashboard' not in response.data.lower()

def test_status_route(client):
    """Test 4: Vérifier que la route /status retourne le bon JSON"""
    response = client.get('/status')
    assert response.status_code == 200
    assert response.json == {"status": "running"}


def test_dashboard_requires_login(client):
    """Test 5: Vérifier que le dashboard est protégé (nécessite connexion)"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/'


def test_dashboard_after_login(client):
    """Test 6: Vérifier que le dashboard est accessible après connexion"""
    client.post('/', data={
        'username': 'admin',
        'password': '1234'
    })
    
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()


def test_logout(client):
    """Test 7: Vérifier que la déconnexion fonctionne"""
    client.post('/', data={
        'username': 'admin',
        'password': '1234'
    })
    
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/'


def test_add_device_authenticated(client):
    """Test 8: Vérifier l'ajout d'un équipement (nécessite connexion)"""
    client.post('/', data={
        'username': 'admin',
        'password': '1234'
    })
    
    response = client.post('/add', data={
        'name': 'Test_Switch_Auto',
        'ip': '192.168.1.200',
        'port': '22',
        'type': 'Switch',
        'location': 'Test Lab',
        'vendor': 'Cisco',
        'description': 'Équipement ajouté par les tests'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'ajout' in response.data.lower() or b'added' in response.data.lower()


def test_add_device_without_login(client):
    """Test 9: Vérifier qu'on ne peut pas ajouter d'équipement sans connexion"""
    response = client.post('/add', data={
        'name': 'Unauthorized_Device',
        'ip': '10.0.0.1',
        'port': '80',
        'type': 'Routeur'
    }, follow_redirects=True)
    
    assert response.request.path == '/'


def test_add_page_access_authenticated(client):
    """Test 10: Vérifier l'accès à la page d'ajout après connexion"""
    client.post('/', data={
        'username': 'admin',
        'password': '1234'
    })
    
    response = client.get('/add')
    assert response.status_code == 200
    assert b'name' in response.data.lower() or b'ajouter' in response.data.lower()


def test_add_page_access_without_login(client):
    """Test 11: Vérifier que la page d'ajout est protégée"""
    response = client.get('/add', follow_redirects=True)
    assert response.request.path == '/'


def test_404_page(client):
    """Test 12: Vérifier que les routes inexistantes retournent 404"""
    response = client.get('/route_qui_n_existe_pas_12345')
    assert response.status_code == 404


def test_session_persistence(client):
    """Test 13: Vérifier que la session reste active entre les requêtes"""
    client.post('/', data={
        'username': 'admin',
        'password': '1234'
    })
    
    response1 = client.get('/dashboard')
    response2 = client.get('/add')
    response3 = client.get('/dashboard')
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200