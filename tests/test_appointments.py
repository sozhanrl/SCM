from datetime import date, timedelta

def test_book_appointment(authenticated_client):
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    res = authenticated_client.post('/api/appointments', json={
        'service_id': 1,
        'appointment_date': tomorrow,
        'start_time': '09:30',
        'notes': 'Please assist with morning vitamins and light walking.'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert 'APT-' in data['data']['appointment_code']
    assert data['data']['status'] == 'Pending'

def test_duplicate_time_slot_prevention(authenticated_client):
    target_date = (date.today() + timedelta(days=3)).isoformat()

    # 1. Book first appointment
    first_res = authenticated_client.post('/api/appointments', json={
        'service_id': 1,
        'appointment_date': target_date,
        'start_time': '11:00',
        'notes': 'First booking'
    })
    assert first_res.status_code == 201

    # 2. Attempt duplicate booking for same user at exact same time slot
    duplicate_res = authenticated_client.post('/api/appointments', json={
        'service_id': 1,
        'appointment_date': target_date,
        'start_time': '11:00',
        'notes': 'Conflicting booking attempt'
    })
    assert duplicate_res.status_code == 400
    assert 'already have a booking' in duplicate_res.get_json()['message']

def test_cancel_appointment(authenticated_client):
    target_date = (date.today() + timedelta(days=4)).isoformat()
    book_res = authenticated_client.post('/api/appointments', json={
        'service_id': 1,
        'appointment_date': target_date,
        'start_time': '13:00',
        'notes': 'To be cancelled'
    })
    app_id = book_res.get_json()['data']['id']

    cancel_res = authenticated_client.patch(f'/api/appointments/{app_id}/cancel', json={
        'reason': 'Family doctor visit rescheduled'
    })
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()['success'] is True

    # Check status changed
    get_res = authenticated_client.get(f'/api/appointments/{app_id}')
    assert get_res.get_json()['data']['status'] == 'Cancelled'

def test_admin_update_appointment_status(client):
    # 1. Log in as user to book appointment
    client.post('/api/auth/login', json={'email': 'user@eldencare.com', 'password': 'User@123456'})
    target_date = (date.today() + timedelta(days=5)).isoformat()
    book_res = client.post('/api/appointments', json={
        'service_id': 1,
        'appointment_date': target_date,
        'start_time': '14:30'
    })
    app_id = book_res.get_json()['data']['id']

    # 2. Log in as admin to update status
    client.post('/api/auth/login', json={'email': 'admin@eldencare.com', 'password': 'Admin@123456'})
    status_res = client.patch(f'/api/admin/appointments/{app_id}/status', json={
        'status': 'Confirmed',
        'reason': 'Caregiver dispatched'
    })
    assert status_res.status_code == 200
    assert status_res.get_json()['success'] is True
