from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import (
    register_user, authenticate_user, change_password,
    request_password_reset, reset_password_with_token
)
from app.utils.decorators import get_current_user, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if get_current_user():
        return redirect(url_for('public.home'))

    if request.method == 'POST':
        form_data = {
            'full_name': request.form.get('full_name', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
            'role': request.form.get('role', 'user')
        }

        user, errors = register_user(form_data)
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html', form_data=form_data)

        flash(f"Registration successful! Your Unique Account Identifier is {user.user_code}. Please log in with your credentials.", 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        user = get_current_user()
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif user.is_caregiver:
            return redirect(url_for('caregiver.dashboard'))
        return redirect(url_for('user.dashboard'))

    next_url = request.args.get('next')

    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user, error = authenticate_user(email, password)
        if error:
            flash(error, 'danger')
            return render_template('auth/login.html', email=email, next=next_url)

        # Establish session
        session.permanent = remember
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name

        flash(f"Welcome back, {user.full_name}!", 'success')

        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif user.is_caregiver:
            return redirect(url_for('caregiver.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html', next=next_url)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been safely logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_pwd():
    user = get_current_user()
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        success, msg = change_password(user, old_password, new_password, confirm_password)
        if success:
            flash(msg, 'success')
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif user.is_caregiver:
                return redirect(url_for('caregiver.dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash(msg, 'danger')

    return render_template('auth/change_password.html', user=user)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    dev_reset_link = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        success, msg, raw_token = request_password_reset(email)
        flash(msg, 'info')
        if raw_token:
            dev_reset_link = url_for('auth.reset_password', token=raw_token, _external=True)

    return render_template('auth/forgot_password.html', dev_reset_link=dev_reset_link)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        success, msg = reset_password_with_token(token, new_password, confirm_password)
        if success:
            flash(msg, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(msg, 'danger')

    return render_template('auth/reset_password.html', token=token)
