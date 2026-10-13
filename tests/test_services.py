def test_admin_create_service(admin_client):
    res = admin_client.post('/api/admin/services', json={
        'name': 'Memory Fitness & Brain Games',
        'category': 'Dementia & Memory Care',
        'price': 45.00,
        'duration_minutes': 60,
        'description': 'Cognitive exercises and memory puzzle therapy.',
        'is_active': True
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'Memory Fitness & Brain Games'

def test_admin_update_service(admin_client):
    res = admin_client.put('/api/admin/services/1', json={
        'name': 'Updated Companionship Visit',
        'category': 'Companionship & Social',
        'price': 38.50,
        'duration_minutes': 75,
        'description': 'Updated description',
        'is_active': True
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['price'] == 38.50
    assert data['data']['duration_minutes'] == 75

def test_non_admin_cannot_create_service(authenticated_client):
    res = authenticated_client.post('/api/admin/services', json={
        'name': 'Unauthorized Service',
        'category': 'Daily Living Assistance',
        'price': 50.00,
        'duration_minutes': 60,
        'description': 'Attempting creation without admin role'
    })
    assert res.status_code == 403

def test_admin_delete_service(admin_client):
    # Create service
    c_res = admin_client.post('/api/admin/services', json={
        'name': 'Temporary Service To Delete',
        'category': 'Nutrition & Meal Prep',
        'price': 25.00,
        'duration_minutes': 60,
        'description': 'Temporary service'
    })
    service_id = c_res.get_json()['data']['id']

    # Delete service
    d_res = admin_client.delete(f'/api/admin/services/{service_id}')
    assert d_res.status_code == 200
    assert d_res.get_json()['success'] is True
