from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils.decorators import login_required, get_current_user
from app.services.user_service import update_user_profile, save_profile_image

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def view_profile():
    user = get_current_user()
    return render_template('user/profile.html', user=user)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = get_current_user()
    if request.method == 'POST':
        form_data = {
            'full_name': request.form.get('full_name', ''),
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', '')
        }
        success, msg = update_user_profile(user, form_data)
        if success:
            flash(msg, 'success')
            return redirect(url_for('profile.view_profile'))
        else:
            flash(msg, 'danger')

    return render_template('user/edit_profile.html', user=user)

@profile_bp.route('/profile/image', methods=['POST'])
@login_required
def upload_image():
    user = get_current_user()
    file = request.files.get('profile_image')
    success, msg, filename = save_profile_image(user, file)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('profile.view_profile'))
