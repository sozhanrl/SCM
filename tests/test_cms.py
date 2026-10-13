import io

def test_admin_create_cms_page(admin_client):
    res = admin_client.post('/api/admin/pages', json={
        'title': 'Emergency Care Protocols',
        'slug': 'emergency-protocols',
        'content': '<p>Details on fall response and medical dispatch.</p>',
        'meta_description': 'Emergency protocols for Elden Care staff',
        'status': 'published'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['slug'] == 'emergency-protocols'

def test_admin_update_cms_page(admin_client):
    # Update page created in conftest (id 1, slug 'home')
    res = admin_client.put('/api/admin/pages/1', json={
        'title': 'Updated Welcome Portal',
        'slug': 'home',
        'content': '<p>Newly updated healthcare content.</p>',
        'status': 'published'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True
    assert res.get_json()['data']['title'] == 'Updated Welcome Portal'

def test_protect_core_cms_pages_from_deletion(admin_client):
    # Attempt to delete core home page
    res = admin_client.delete('/api/admin/pages/1')
    assert res.status_code == 400
    assert 'core system page' in res.get_json()['message']

def test_cms_media_upload_and_delete(admin_client):
    img_data = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4'
                b'\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\r\xef\x00\x00\x00\x00IEND\xaeB`\x82')
    data = {
        'media_file': (io.BytesIO(img_data), 'clinic_banner.png'),
        'caption': 'Clinic entrance banner'
    }
    upload_res = admin_client.post('/api/admin/media', data=data, content_type='multipart/form-data')
    assert upload_res.status_code == 201
    media_id = upload_res.get_json()['data']['id']

    # Delete media
    del_res = admin_client.delete(f'/api/admin/media/{media_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True
