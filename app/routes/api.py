from flask import Blueprint, request, jsonify, session
from datetime import date
from app.extensions import db
from app.utils.decorators import get_current_user, login_required, admin_required, role_required
from app.services.auth_service import (
    register_user, authenticate_user, change_password,
    request_password_reset, reset_password_with_token
)
from app.services.user_service import (
    get_user_by_id, update_user_profile, save_profile_image,
    get_all_users, admin_update_user, admin_toggle_user_status
)
from app.services.service_service import (
    get_services, get_service_by_id, create_service, update_service, delete_service
)
from app.services.appointment_service import (
    book_appointment, cancel_appointment, update_appointment_status, get_available_time_slots
)
from app.services.cms_service import (
    get_all_pages, get_page_by_slug, create_page, update_page, delete_page,
    get_all_media, save_media, delete_media
)
from app.models.user import User
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.cms import Page, Media

api_bp = Blueprint('api', __name__, url_prefix='/api')

def json_response(success: bool, message: str = "", data=None, status_code: int = 200):
    payload = {
        'success': success,
        'message': message
    }
    if data is not None:
        payload['data'] = data
    return jsonify(payload), status_code

# ================= AUTHENTICATION APIS =================
@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or request.form.to_dict()
    user, errors = register_user(data)
    if errors:
        return json_response(False, "; ".join(errors), status_code=400)
    return json_response(True, f"User registered successfully with ID {user.user_code}", user.to_dict(), status_code=201)

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = data.get('email', '')
    password = data.get('password', '')
    user, error = authenticate_user(email, password)
    if error:
        return json_response(False, error, status_code=401)

    session['user_id'] = user.id
    session['user_role'] = user.role
    session['user_name'] = user.full_name
    return json_response(True, "Login successful", user.to_dict())

@api_bp.route('/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return json_response(True, "Successfully logged out")

@api_bp.route('/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    user = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    old_p = data.get('old_password', '')
    new_p = data.get('new_password', '')
    confirm_p = data.get('confirm_password', '')

    success, msg = change_password(user, old_p, new_p, confirm_p)
    return json_response(success, msg, status_code=200 if success else 400)

@api_bp.route('/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = data.get('email', '')
    success, msg, raw_token = request_password_reset(email)
    payload = {'reset_token': raw_token} if raw_token else None
    return json_response(success, msg, payload, status_code=200 if success else 400)

@api_bp.route('/auth/reset-password', methods=['POST'])
def api_reset_password():
    data = request.get_json(silent=True) or request.form.to_dict()
    token = data.get('token', '')
    new_p = data.get('new_password', '')
    confirm_p = data.get('confirm_password', '')

    success, msg = reset_password_with_token(token, new_p, confirm_p)
    return json_response(success, msg, status_code=200 if success else 400)

# ================= PROFILE APIS =================
@api_bp.route('/profile', methods=['GET'])
@login_required
def api_get_profile():
    user = get_current_user()
    return json_response(True, "Profile retrieved", user.to_dict())

@api_bp.route('/profile', methods=['PUT'])
@login_required
def api_update_profile():
    user = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    success, msg = update_user_profile(user, data)
    if success:
        return json_response(True, msg, user.to_dict())
    return json_response(False, msg, status_code=400)

@api_bp.route('/profile/image', methods=['POST'])
@login_required
def api_upload_profile_image():
    user = get_current_user()
    file = request.files.get('profile_image')
    success, msg, filename = save_profile_image(user, file)
    if success:
        return json_response(True, msg, {'profile_image': filename, 'avatar_url': user.get_avatar_url()})
    return json_response(False, msg, status_code=400)

# ================= ADMIN USER APIS =================
@api_bp.route('/admin/users', methods=['GET'])
@admin_required
def api_admin_list_users():
    search = request.args.get('search')
    role = request.args.get('role')
    status = request.args.get('status')
    users = get_all_users(search=search, role=role, status=status)
    return json_response(True, "Users retrieved", [u.to_dict() for u in users])

@api_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def api_admin_get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return json_response(False, "User not found", status_code=404)
    return json_response(True, "User details retrieved", user.to_dict())

@api_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def api_admin_update_user(user_id):
    admin = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    success, msg = admin_update_user(user_id, data, admin_id=admin.id)
    if success:
        target = get_user_by_id(user_id)
        return json_response(True, msg, target.to_dict())
    return json_response(False, msg, status_code=400)

@api_bp.route('/admin/users/<int:user_id>/status', methods=['PATCH'])
@admin_required
def api_admin_toggle_user_status(user_id):
    admin = get_current_user()
    success, msg = admin_toggle_user_status(user_id, admin_id=admin.id)
    if success:
        target = get_user_by_id(user_id)
        return json_response(True, msg, {'is_active': target.is_active})
    return json_response(False, msg, status_code=400)

# ================= SERVICES APIS =================
@api_bp.route('/services', methods=['GET'])
def api_list_services():
    search = request.args.get('search')
    category = request.args.get('category')
    active_only = request.args.get('active_only', 'false').lower() in ('true', '1')
    services = get_services(search=search, category=category, active_only=active_only)
    return json_response(True, "Services retrieved", [s.to_dict() for s in services])

@api_bp.route('/admin/services', methods=['POST'])
@admin_required
def api_admin_create_service():
    admin = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    service, errors = create_service(data, admin_id=admin.id)
    if errors:
        return json_response(False, "; ".join(errors), status_code=400)
    return json_response(True, "Service created", service.to_dict(), status_code=201)

@api_bp.route('/admin/services/<int:service_id>', methods=['PUT'])
@admin_required
def api_admin_update_service(service_id):
    admin = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    service, errors = update_service(service_id, data, admin_id=admin.id)
    if errors:
        return json_response(False, "; ".join(errors), status_code=400)
    return json_response(True, "Service updated", service.to_dict())

@api_bp.route('/admin/services/<int:service_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_service(service_id):
    admin = get_current_user()
    success, msg = delete_service(service_id, admin_id=admin.id)
    return json_response(success, msg, status_code=200 if success else 400)

# ================= APPOINTMENTS APIS =================
@api_bp.route('/appointments/available-slots', methods=['GET'])
def api_available_slots():
    date_str = request.args.get('date', date.today().isoformat())
    provider_id = request.args.get('provider_id', type=int)
    slots = get_available_time_slots(date_str, provider_id=provider_id)
    return json_response(True, "Available slots", slots)

@api_bp.route('/appointments', methods=['GET'])
@login_required
def api_list_appointments():
    user = get_current_user()
    if user.is_admin:
        status = request.args.get('status')
        query = Appointment.query
        if status and status != 'all':
            query = query.filter_by(status=status)
        appointments = query.order_by(Appointment.appointment_date.desc()).all()
    elif user.is_caregiver:
        appointments = Appointment.query.filter_by(provider_id=user.id).order_by(Appointment.appointment_date.desc()).all()
    else:
        appointments = Appointment.query.filter_by(user_id=user.id).order_by(Appointment.appointment_date.desc()).all()

    return json_response(True, "Appointments retrieved", [a.to_dict() for a in appointments])

@api_bp.route('/appointments', methods=['POST'])
@login_required
def api_book_appointment():
    user = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()

    service_id = data.get('service_id')
    appointment_date = data.get('appointment_date')
    start_time = data.get('start_time')
    notes = data.get('notes')
    provider_id = data.get('provider_id')

    if not service_id or not appointment_date or not start_time:
        return json_response(False, "service_id, appointment_date, and start_time are required", status_code=400)

    appointment, errors = book_appointment(
        user_id=user.id,
        service_id=int(service_id),
        appointment_date_str=appointment_date,
        start_time_str=start_time,
        notes=notes,
        provider_id=int(provider_id) if provider_id else None
    )

    if errors:
        return json_response(False, "; ".join(errors), status_code=400)

    return json_response(True, f"Appointment {appointment.appointment_code} booked successfully", appointment.to_dict(), status_code=201)

@api_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@login_required
def api_get_appointment(appointment_id):
    user = get_current_user()
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return json_response(False, "Appointment not found", status_code=404)

    # Permission check
    if not user.is_admin and appointment.user_id != user.id and appointment.provider_id != user.id:
        return json_response(False, "Access forbidden", status_code=403)

    return json_response(True, "Appointment retrieved", appointment.to_dict())

@api_bp.route('/appointments/<int:appointment_id>/cancel', methods=['PATCH'])
@login_required
def api_cancel_appointment(appointment_id):
    user = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = data.get('reason', 'Cancelled via API')

    success, msg = cancel_appointment(appointment_id, user_id=user.id, is_admin=user.is_admin, reason=reason)
    return json_response(success, msg, status_code=200 if success else 400)

@api_bp.route('/admin/appointments/<int:appointment_id>/status', methods=['PATCH'])
@role_required('admin', 'caregiver')
def api_update_appointment_status(appointment_id):
    user = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    new_status = data.get('status')
    reason = data.get('reason')
    provider_id = data.get('provider_id')

    if not new_status:
        return json_response(False, "Status is required", status_code=400)

    success, msg = update_appointment_status(
        appointment_id,
        new_status,
        updater=user,
        reason=reason,
        provider_id=int(provider_id) if provider_id is not None else None
    )
    return json_response(success, msg, status_code=200 if success else 400)

# ================= CMS APIS =================
@api_bp.route('/pages', methods=['GET'])
def api_list_pages():
    pages = get_all_pages(status='published')
    return json_response(True, "Pages retrieved", [p.to_dict() for p in pages])

@api_bp.route('/admin/pages', methods=['POST'])
@admin_required
def api_create_page():
    admin = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    page, errors = create_page(data, author_id=admin.id)
    if errors:
        return json_response(False, "; ".join(errors), status_code=400)
    return json_response(True, "Page created", page.to_dict(), status_code=201)

@api_bp.route('/admin/pages/<int:page_id>', methods=['PUT'])
@admin_required
def api_update_page(page_id):
    admin = get_current_user()
    data = request.get_json(silent=True) or request.form.to_dict()
    page, errors = update_page(page_id, data, author_id=admin.id)
    if errors:
        return json_response(False, "; ".join(errors), status_code=400)
    return json_response(True, "Page updated", page.to_dict())

@api_bp.route('/admin/pages/<int:page_id>', methods=['DELETE'])
@admin_required
def api_delete_page(page_id):
    admin = get_current_user()
    success, msg = delete_page(page_id, admin_id=admin.id)
    return json_response(success, msg, status_code=200 if success else 400)

@api_bp.route('/admin/media', methods=['GET'])
@admin_required
def api_list_media():
    items = get_all_media()
    return json_response(True, "Media items", [m.to_dict() for m in items])

@api_bp.route('/admin/media', methods=['POST'])
@admin_required
def api_upload_media():
    admin = get_current_user()
    file = request.files.get('media_file')
    caption = request.form.get('caption', '')
    media_obj, err = save_media(file, uploader_id=admin.id, caption=caption)
    if err:
        return json_response(False, err, status_code=400)
    return json_response(True, "Media uploaded", media_obj.to_dict(), status_code=201)

@api_bp.route('/admin/media/<int:media_id>', methods=['DELETE'])
@admin_required
def api_delete_media(media_id):
    admin = get_current_user()
    success, msg = delete_media(media_id, admin_id=admin.id)
    return json_response(success, msg, status_code=200 if success else 400)
