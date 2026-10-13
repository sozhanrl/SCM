import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.services.activity_service import log_activity

def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)

def get_user_by_code(user_code: str) -> User | None:
    return User.query.filter_by(user_code=user_code).first()

def update_user_profile(user: User, data: dict) -> tuple[bool, str]:
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()

    if not full_name:
        return False, "Full name cannot be empty."

    try:
        user.full_name = full_name
        user.phone = phone or None
        user.address = address or None
        db.session.commit()
        log_activity('PROFILE_UPDATED', user_id=user.id, details="User updated profile details")
        return True, "Profile details updated successfully."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to update profile: {str(e)}"

def save_profile_image(user: User, file_storage) -> tuple[bool, str, str | None]:
    if not file_storage or file_storage.filename == '':
        return False, "No file was selected for upload.", None

    filename = secure_filename(file_storage.filename)
    if not filename:
        return False, "Invalid filename.", None

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    allowed_exts = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
    if ext not in allowed_exts:
        return False, f"File type '.{ext}' is not supported. Allowed formats: {', '.join(allowed_exts)}.", None

    # Check size (reading length)
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    max_size = 5 * 1024 * 1024 # 5 MB for profile avatar
    if size > max_size:
        return False, "Image size exceeds 5 MB limit.", None

    # Generate unique filename to prevent overwrite/enumeration
    unique_filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_folder = current_app.config['PROFILE_UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, unique_filename)

    try:
        file_storage.save(save_path)

        # Remove old image if not default
        if user.profile_image and user.profile_image != unique_filename:
            old_path = os.path.join(upload_folder, user.profile_image)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass

        user.profile_image = unique_filename
        db.session.commit()
        log_activity('PROFILE_IMAGE_UPLOADED', user_id=user.id, details=f"Profile picture uploaded: {unique_filename}")
        return True, "Profile picture uploaded successfully.", unique_filename
    except Exception as e:
        db.session.rollback()
        return False, f"Error saving image: {str(e)}", None

def get_all_users(search: str = None, role: str = None, status: str = None):
    query = User.query
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (User.email.ilike(s)) | (User.user_code.ilike(s)))
    if role and role != 'all':
        query = query.filter(User.role == role)
    if status and status != 'all':
        is_active = (status == 'active')
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.created_at.desc()).all()

def admin_update_user(user_id: int, data: dict, admin_id: int) -> tuple[bool, str]:
    target_user = db.session.get(User, user_id)
    if not target_user:
        return False, "User not found."

    # Cannot demote or disable self
    if target_user.id == admin_id and data.get('role') != 'admin':
        return False, "You cannot remove your own administrator status."

    try:
        if 'full_name' in data and data['full_name'].strip():
            target_user.full_name = data['full_name'].strip()
        if 'phone' in data:
            target_user.phone = data['phone'].strip() or None
        if 'address' in data:
            target_user.address = data['address'].strip() or None
        if 'role' in data and data['role'] in ('admin', 'user', 'caregiver'):
            target_user.role = data['role']
        if 'is_active' in data:
            target_user.is_active = bool(data['is_active'])

        db.session.commit()
        log_activity('ADMIN_USER_UPDATED', user_id=admin_id, details=f"Admin updated user {target_user.email} (ID: {target_user.id})")
        return True, "User updated successfully."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to update user: {str(e)}"

def admin_toggle_user_status(user_id: int, admin_id: int) -> tuple[bool, str]:
    target_user = db.session.get(User, user_id)
    if not target_user:
        return False, "User not found."

    if target_user.id == admin_id:
        return False, "You cannot deactivate your own administrator account."

    try:
        target_user.is_active = not target_user.is_active
        db.session.commit()
        status_text = "activated" if target_user.is_active else "deactivated"
        log_activity('ADMIN_USER_STATUS_TOGGLED', user_id=admin_id, details=f"User {target_user.email} was {status_text}")
        return True, f"User account has been {status_text}."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to change status: {str(e)}"
