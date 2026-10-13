import io

def test_get_profile(authenticated_client):
    res = authenticated_client.get('/api/profile')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['email'] == 'user@eldencare.com'
    assert 'USR-TESTUSER' in data['data']['user_code']

def test_update_profile(authenticated_client):
    res = authenticated_client.put('/api/profile', json={
        'full_name': 'Updated Eleanor Vance',
        'phone': '+1 (555) 999-0000',
        'address': '104 Sunset Boulevard'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['full_name'] == 'Updated Eleanor Vance'
    assert data['data']['phone'] == '+1 (555) 999-0000'

def test_profile_image_upload(authenticated_client):
    # Simulated PNG image upload
    img_data = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4'
                b'\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\r\xef\x00\x00\x00\x00IEND\xaeB`\x82')
    data = {
        'profile_image': (io.BytesIO(img_data), 'test_avatar.png')
    }
    res = authenticated_client.post('/api/profile/image', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    res_data = res.get_json()
    assert res_data['success'] is True
    assert 'user_' in res_data['data']['profile_image']

def test_profile_image_invalid_extension(authenticated_client):
    data = {
        'profile_image': (io.BytesIO(b'malicious script'), 'exploit.exe')
    }
    res = authenticated_client.post('/api/profile/image', data=data, content_type='multipart/form-data')
    assert res.status_code == 400
    assert 'not supported' in res.get_json()['message']
