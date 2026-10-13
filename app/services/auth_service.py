import re
from datetime import datetime, timezone
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.models.token import PasswordResetToken, EmailVerificationToken
from app.services.activity_service import log_activity

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

def validate_registration_input(data: dict) -> list[str]:
    errors = []
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    phone = data.get('phone', '').strip()
    role = data.get('role', 'user').strip().lower()

    if not full_name:
        errors.append("Full name is required.")
    elif len(full_name) < 2:
        errors.append("Full name must be at least 2 characters.")

    if not email:
        errors.append("Email address is required.")
    elif not EMAIL_REGEX.match(email):
        errors.append("Please provide a valid email address.")
    else:
        existing = User.query.filter_by(email=email).first()
        if existing:
            errors.append("An account with this email address already exists.")

    if not password:
        errors.append("Password is required.")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters.")

    if password != confirm_password:
        errors.append("Password confirmation does not match.")

    # Restrict public role registration - cannot register as admin
    if role not in ('user', 'caregiver'):
        errors.append("Selected role is invalid. Allowed roles are 'user' (Care Recipient) or 'caregiver'.")

    return errors

def register_user(data: dict) -> tuple[User | None, list[str]]:
    """Registers a new user into the database."""
    errors = validate_registration_input(data)
    if errors:
        return None, errors

    try:
        user = User(
            full_name=data['full_name'].strip(),
            email=data['email'].strip().lower(),
            phone=data.get('phone', '').strip() or None,
            address=data.get('address', '').strip() or None,
            role=data.get('role', 'user').strip().lower(),
            is_active=True,
            email_verified=False
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        log_activity('USER_REGISTERED', user_id=user.id, details=f"User {user.email} registered with code {user.user_code}")
        return user, []
    except Exception as e:
        db.session.rollback()
        return None, [f"Registration error: {str(e)}"]

def authenticate_user(email: str, password: str) -> tuple[User | None, str | None]:
    """Authenticates a user securely. Rejects incorrect passwords or inactive accounts."""
    if not email or not password:
        return None, "Email and password are required."

    cleaned_email = email.strip().lower()
    user = User.query.filter_by(email=cleaned_email).first()

    if not user:
        return None, "Invalid email or password."

    if not user.is_active:
        return None, "This account has been deactivated. Please contact support."

    if not user.check_password(password):
        log_activity('LOGIN_FAILED', user_id=user.id, details=f"Failed login attempt for {cleaned_email}")
        return None, "Invalid email or password."

    log_activity('USER_LOGIN', user_id=user.id, details=f"User {user.email} logged in successfully")
    return user, None

def change_password(user: User, old_password: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """Changes password after verifying old password and validating new password."""
    if not old_password or not new_password or not confirm_password:
        return False, "All password fields are required."

    if not user.check_password(old_password):
        return False, "Current password is incorrect."

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    if new_password != confirm_password:
        return False, "New password confirmation does not match."

    if old_password == new_password:
        return False, "New password cannot be the same as the old password."

    try:
        user.set_password(new_password)
        db.session.commit()
        log_activity('PASSWORD_CHANGED', user_id=user.id, details="Password changed successfully")
        return True, "Password has been successfully updated."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to update password: {str(e)}"

def request_password_reset(email: str) -> tuple[bool, str, str | None]:
    """Generates a secure password reset token."""
    if not email:
        return False, "Email address is required.", None

    cleaned_email = email.strip().lower()
    user = User.query.filter_by(email=cleaned_email).first()

    if not user:
        # Prevent account enumeration: return success message even if email not found
        return True, "If an account exists with that email, a password reset link has been generated.", None

    if not user.is_active:
        return False, "This account is inactive.", None

    # Invalidate previous unused tokens for this user
    PasswordResetToken.query.filter_by(user_id=user.id, is_used=False).update({'is_used': True})

    exp_seconds = current_app.config.get('RESET_TOKEN_EXPIRATION_SECONDS', 3600)
    token_obj, raw_token = PasswordResetToken.generate_token(user.id, expires_in_seconds=exp_seconds)
    
    db.session.add(token_obj)
    db.session.commit()

    log_activity('PASSWORD_RESET_REQUESTED', user_id=user.id, details=f"Reset token generated for {cleaned_email}")
    return True, "A password reset link has been generated.", raw_token

def reset_password_with_token(raw_token: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """Validates single-use token and updates user password."""
    if not raw_token:
        return False, "Reset token is missing."

    if not new_password or not confirm_password:
        return False, "New password and confirmation are required."

    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."

    if new_password != confirm_password:
        return False, "Password confirmation does not match."

    token_hash = PasswordResetToken.hash_token(raw_token)
    token_entry = PasswordResetToken.query.filter_by(token_hash=token_hash).first()

    if not token_entry or not token_entry.is_valid():
        return False, "The reset link is invalid or has expired. Please request a new one."

    user = db.session.get(User, token_entry.user_id)
    if not user or not user.is_active:
        return False, "Associated user account not found or deactivated."

    try:
        user.set_password(new_password)
        token_entry.is_used = True
        db.session.commit()
        log_activity('PASSWORD_RESET_COMPLETED', user_id=user.id, details="Password reset via token")
        return True, "Your password has been successfully reset. You may now log in."
    except Exception as e:
        db.session.rollback()
        return False, f"Could not reset password: {str(e)}"
