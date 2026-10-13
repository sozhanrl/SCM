def test_admin_list_users(admin_client):
    res = admin_client.get('/api/admin/users')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['data']) >= 3

def test_admin_toggle_user_status(admin_client):
    # Find user ID 3 (the test user)
    res = admin_client.patch('/api/admin/users/3/status')
    assert res.status_code == 200
    assert res.get_json()['data']['is_active'] is False

    # Toggle back to active
    res_back = admin_client.patch('/api/admin/users/3/status')
    assert res_back.status_code == 200
    assert res_back.get_json()['data']['is_active'] is True

def test_admin_cannot_deactivate_self(admin_client):
    # Admin is ID 1
    res = admin_client.patch('/api/admin/users/1/status')
    assert res.status_code == 400
    assert 'cannot deactivate your own' in res.get_json()['message']

def test_unauthorized_user_cannot_access_admin_api(authenticated_client):
    res = authenticated_client.get('/api/admin/users')
    assert res.status_code == 403
