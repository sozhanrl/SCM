def test_successful_registration(client):
    res = client.post('/api/auth/register', json={
        'full_name': 'New Elder Client',
        'email': 'newclient@eldencare.com',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'phone': '+1 (555) 888-9999',
        'address': '55 Oak Avenue',
        'role': 'user'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert 'USR-' in data['data']['user_code']
    assert data['data']['email'] == 'newclient@eldencare.com'

def test_duplicate_email_registration(client):
    res = client.post('/api/auth/register', json={
        'full_name': 'Duplicate User',
        'email': 'user@eldencare.com',  # Already exists in conftest
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'role': 'user'
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'already exists' in data['message']

def test_registration_validation(client):
    # Password mismatch
    res = client.post('/api/auth/register', json={
        'full_name': 'Mismatch User',
        'email': 'mismatch@example.com',
        'password': 'Password@123',
        'confirm_password': 'DifferentPassword',
        'role': 'user'
    })
    assert res.status_code == 400

    # Role restriction: cannot register as admin publicly
    res2 = client.post('/api/auth/register', json={
        'full_name': 'Hacker Admin',
        'email': 'hacker@example.com',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'role': 'admin'
    })
    assert res2.status_code == 400

def test_login_valid_credentials(client):
    res = client.post('/api/auth/login', json={
        'email': 'user@eldencare.com',
        'password': 'User@123456'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['email'] == 'user@eldencare.com'

def test_login_incorrect_credentials(client):
    res = client.post('/api/auth/login', json={
        'email': 'user@eldencare.com',
        'password': 'WrongPassword123'
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data['success'] is False
    assert 'Invalid email or password' in data['message']

def test_unauthorized_dashboard_access(client):
    # Unauthenticated attempt to access user dashboard
    res = client.get('/dashboard')
    # Should redirect to login
    assert res.status_code == 302
    assert '/login' in res.headers['Location']

    # Unauthenticated attempt to access admin dashboard
    res_admin = client.get('/admin/dashboard')
    assert res_admin.status_code == 302
    assert '/login' in res_admin.headers['Location']

def test_role_enforcement_non_admin_blocked(authenticated_client):
    # Regular user attempting admin dashboard
    res = authenticated_client.get('/admin/dashboard')
    assert res.status_code == 302 # Redirected away due to forbidden role
    assert '/dashboard' in res.headers['Location']

def test_password_change(authenticated_client):
    # Valid change
    res = authenticated_client.post('/api/auth/change-password', json={
        'old_password': 'User@123456',
        'new_password': 'BrandNewPassword@99',
        'confirm_password': 'BrandNewPassword@99'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    # Check new password works
    login_res = authenticated_client.post('/api/auth/login', json={
        'email': 'user@eldencare.com',
        'password': 'BrandNewPassword@99'
    })
    assert login_res.status_code == 200

def test_password_reset_flow(client):
    # 1. Request reset
    req_res = client.post('/api/auth/forgot-password', json={
        'email': 'user@eldencare.com'
    })
    assert req_res.status_code == 200
    token = req_res.get_json()['data']['reset_token']
    assert token is not None

    # 2. Reset with token
    reset_res = client.post('/api/auth/reset-password', json={
        'token': token,
        'new_password': 'ResetPass@2026',
        'confirm_password': 'ResetPass@2026'
    })
    assert reset_res.status_code == 200
    assert reset_res.get_json()['success'] is True

    # 3. Ensure token is single-use: cannot be reused
    reuse_res = client.post('/api/auth/reset-password', json={
        'token': token,
        'new_password': 'AnotherPass@2026',
        'confirm_password': 'AnotherPass@2026'
    })
    assert reuse_res.status_code == 400
