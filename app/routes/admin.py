from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils.decorators import admin_required, get_current_user
from app.models.user import User
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.cms import Page, Media
from app.models.activity import ActivityLog
from app.services.user_service import get_all_users, admin_update_user, admin_toggle_user_status
from app.services.service_service import (
    get_services, create_service, update_service, delete_service, CATEGORIES
)
from app.services.appointment_service import update_appointment_status, cancel_appointment
from app.services.cms_service import (
    get_all_pages, create_page, update_page, delete_page,
    get_all_media, save_media, delete_media
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    admin = get_current_user()
    
    total_users = User.query.filter_by(role='user').count()
    total_caregivers = User.query.filter_by(role='caregiver').count()
    total_services = Service.query.count()
    active_services = Service.query.filter_by(is_active=True).count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='Pending').count()
    confirmed_appointments = Appointment.query.filter_by(status='Confirmed').count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()

    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(6).all()
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        admin=admin,
        total_users=total_users,
        total_caregivers=total_caregivers,
        total_services=total_services,
        active_services=active_services,
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        confirmed_appointments=confirmed_appointments,
        completed_appointments=completed_appointments,
        recent_appointments=recent_appointments,
        recent_activity=recent_activity
    )

# ----------------- User Management -----------------
@admin_bp.route('/users')
@admin_required
def users():
    search = request.args.get('search')
    role = request.args.get('role')
    status = request.args.get('status')
    user_list = get_all_users(search=search, role=role, status=status)
    return render_template('admin/users.html', users=user_list, search=search, role=role, status=status)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    admin = get_current_user()
    target_user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        form_data = {
            'full_name': request.form.get('full_name', ''),
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'role': request.form.get('role', ''),
            'is_active': bool(request.form.get('is_active'))
        }
        success, msg = admin_update_user(user_id, form_data, admin_id=admin.id)
        if success:
            flash(msg, 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(msg, 'danger')

    return render_template('admin/edit_user.html', target_user=target_user)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    admin = get_current_user()
    success, msg = admin_toggle_user_status(user_id, admin_id=admin.id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('admin.users'))

# ----------------- Service Management -----------------
@admin_bp.route('/services')
@admin_required
def services():
    search = request.args.get('search')
    category = request.args.get('category')
    service_list = get_services(search=search, category=category)
    return render_template('admin/services.html', services=service_list, categories=CATEGORIES, search=search, category=category)

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@admin_required
def add_service():
    admin = get_current_user()
    if request.method == 'POST':
        form_data = {
            'name': request.form.get('name', ''),
            'category': request.form.get('category', ''),
            'price': request.form.get('price', '0'),
            'duration_minutes': request.form.get('duration_minutes', '60'),
            'description': request.form.get('description', ''),
            'image_path': request.form.get('image_path', ''),
            'is_active': bool(request.form.get('is_active'))
        }
        service, errors = create_service(form_data, admin_id=admin.id)
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/service_form.html', form_data=form_data, categories=CATEGORIES, is_edit=False)

        flash(f"Service '{service.name}' created successfully!", 'success')
        return redirect(url_for('admin.services'))

    return render_template('admin/service_form.html', form_data={}, categories=CATEGORIES, is_edit=False)

@admin_bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_service_route(service_id):
    admin = get_current_user()
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        form_data = {
            'name': request.form.get('name', ''),
            'category': request.form.get('category', ''),
            'price': request.form.get('price', '0'),
            'duration_minutes': request.form.get('duration_minutes', '60'),
            'description': request.form.get('description', ''),
            'image_path': request.form.get('image_path', ''),
            'is_active': bool(request.form.get('is_active'))
        }
        updated, errors = update_service(service_id, form_data, admin_id=admin.id)
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/service_form.html', form_data=form_data, service=service, categories=CATEGORIES, is_edit=True)

        flash(f"Service '{service.name}' updated successfully!", 'success')
        return redirect(url_for('admin.services'))

    form_data = service.to_dict()
    return render_template('admin/service_form.html', form_data=form_data, service=service, categories=CATEGORIES, is_edit=True)

@admin_bp.route('/services/<int:service_id>/delete', methods=['POST'])
@admin_required
def delete_service_route(service_id):
    admin = get_current_user()
    success, msg = delete_service(service_id, admin_id=admin.id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('admin.services'))

# ----------------- Appointment Management -----------------
@admin_bp.route('/appointments')
@admin_required
def appointments():
    status = request.args.get('status')
    search = request.args.get('search')
    query = Appointment.query
    if status and status != 'all':
        query = query.filter_by(status=status)
    if search:
        s = f"%{search.strip()}%"
        query = query.join(User, Appointment.user_id == User.id).filter(
            (Appointment.appointment_code.ilike(s)) | (User.full_name.ilike(s)) | (User.email.ilike(s))
        )
    appointment_list = query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.asc()).all()
    caregivers = User.query.filter_by(role='caregiver', is_active=True).all()
    return render_template('admin/appointments.html', appointments=appointment_list, caregivers=caregivers, status=status, search=search)

@admin_bp.route('/appointments/<int:appointment_id>/status', methods=['POST'])
@admin_required
def update_appointment_status_route(appointment_id):
    admin = get_current_user()
    new_status = request.form.get('status')
    notes = request.form.get('notes')
    provider_id = request.form.get('provider_id', type=int)

    success, msg = update_appointment_status(appointment_id, new_status, updater=admin, reason=notes, provider_id=provider_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('admin.appointments'))

# ----------------- CMS: Pages Management -----------------
@admin_bp.route('/pages')
@admin_required
def pages():
    page_list = get_all_pages()
    return render_template('admin/pages.html', pages=page_list)

@admin_bp.route('/pages/new', methods=['GET', 'POST'])
@admin_required
def add_page():
    admin = get_current_user()
    if request.method == 'POST':
        form_data = {
            'title': request.form.get('title', ''),
            'slug': request.form.get('slug', ''),
            'content': request.form.get('content', ''),
            'meta_description': request.form.get('meta_description', ''),
            'status': request.form.get('status', 'published')
        }
        page, errors = create_page(form_data, author_id=admin.id)
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/page_form.html', form_data=form_data, is_edit=False)

        flash(f"Page '{page.title}' created successfully!", 'success')
        return redirect(url_for('admin.pages'))

    return render_template('admin/page_form.html', form_data={}, is_edit=False)

@admin_bp.route('/pages/<int:page_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_page_route(page_id):
    admin = get_current_user()
    page = Page.query.get_or_404(page_id)

    if request.method == 'POST':
        form_data = {
            'title': request.form.get('title', ''),
            'slug': request.form.get('slug', ''),
            'content': request.form.get('content', ''),
            'meta_description': request.form.get('meta_description', ''),
            'status': request.form.get('status', 'published')
        }
        updated, errors = update_page(page_id, form_data, author_id=admin.id)
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/page_form.html', form_data=form_data, page=page, is_edit=True)

        flash(f"Page '{page.title}' updated successfully!", 'success')
        return redirect(url_for('admin.pages'))

    form_data = page.to_dict()
    return render_template('admin/page_form.html', form_data=form_data, page=page, is_edit=True)

@admin_bp.route('/pages/<int:page_id>/delete', methods=['POST'])
@admin_required
def delete_page_route(page_id):
    admin = get_current_user()
    success, msg = delete_page(page_id, admin_id=admin.id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('admin.pages'))

# ----------------- CMS: Media Management -----------------
@admin_bp.route('/media', methods=['GET', 'POST'])
@admin_required
def media():
    admin = get_current_user()
    if request.method == 'POST':
        file = request.files.get('media_file')
        caption = request.form.get('caption', '')
        media_obj, err = save_media(file, uploader_id=admin.id, caption=caption)
        if err:
            flash(err, 'danger')
        else:
            flash(f"Media '{media_obj.original_filename}' uploaded successfully!", 'success')
        return redirect(url_for('admin.media'))

    media_items = get_all_media()
    return render_template('admin/media.html', media_items=media_items)

@admin_bp.route('/media/<int:media_id>/delete', methods=['POST'])
@admin_required
def delete_media_route(media_id):
    admin = get_current_user()
    success, msg = delete_media(media_id, admin_id=admin.id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('admin.media'))

# ----------------- Activity Logs -----------------
@admin_bp.route('/logs')
@admin_required
def activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    return render_template('admin/logs.html', logs=logs)
