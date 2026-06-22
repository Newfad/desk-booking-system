import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200

def test_login_invalid_credentials(client):
    response = client.post('/login', data={
        'email': 'wrong@northumbria.ac.uk',
        'password': 'wrongpassword'
    })
    assert b'Invalid email or password' in response.data

def test_register_page_loads(client):
    response = client.get('/register')
    assert response.status_code == 200

def test_admin_redirect_without_login(client):
    response = client.get('/admin')
    assert response.status_code == 302

def test_desks_redirect_without_login(client):
    response = client.get('/desks')
    assert response.status_code == 302