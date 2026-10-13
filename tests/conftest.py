import pytest
import io
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.service import Service
from app.models.cms import Page

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        # Seed Test Admin
        admin = User(
            user_code='USR-TESTADMIN',
            full_name='Test Admin',
            email='admin@eldencare.com',
            role='admin',
            is_active=True,
            email_verified=True
        )
        admin.set_password('Admin@123456')
        db.session.add(admin)

        # Seed Test Caregiver
        cg = User(
            user_code='USR-TESTCG',
            full_name='Test Caregiver',
            email='caregiver@eldencare.com',
            role='caregiver',
            is_active=True,
            email_verified=True
        )
        cg.set_password('Caregiver@123')
        db.session.add(cg)

        # Seed Test User
        user = User(
            user_code='USR-TESTUSER',
            full_name='Test User',
            email='user@eldencare.com',
            role='user',
            is_active=True,
            email_verified=True
        )
        user.set_password('User@123456')
        db.session.add(user)

        # Seed Test Service
        svc = Service(
            service_code='SVC-TEST1',
            name='Test Companionship',
            category='Companionship & Social',
            price=30.00,
            duration_minutes=60,
            description='Friendly companionship care for tests',
            is_active=True
        )
        db.session.add(svc)

        # Seed Test Page
        page = Page(
            title='Test Home',
            slug='home',
            content='<p>Welcome to Test Home</p>',
            status='published'
        )
        db.session.add(page)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_client(client):
    """Logs in as regular user."""
    client.post('/api/auth/login', json={
        'email': 'user@eldencare.com',
        'password': 'User@123456'
    })
    return client

@pytest.fixture
def admin_client(client):
    """Logs in as admin."""
    client.post('/api/auth/login', json={
        'email': 'admin@eldencare.com',
        'password': 'Admin@123456'
    })
    return client

@pytest.fixture
def caregiver_client(client):
    """Logs in as caregiver."""
    client.post('/api/auth/login', json={
        'email': 'caregiver@eldencare.com',
        'password': 'Caregiver@123'
    })
    return client
