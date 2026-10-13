from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date
from app.utils.decorators import login_required, role_required, get_current_user
from app.models.appointment import Appointment
from app.services.appointment_service import update_appointment_status

caregiver_bp = Blueprint('caregiver', __name__)

@caregiver_bp.route('/dashboard')
@login_required
@role_required('caregiver', 'admin')
def dashboard():
    user = get_current_user()
    today = date.today()

    today_appointments = Appointment.query.filter(
        Appointment.provider_id == user.id,
        Appointment.appointment_date == today,
        Appointment.status != 'Cancelled'
    ).order_by(Appointment.start_time.asc()).all()

    upcoming_appointments = Appointment.query.filter(
        Appointment.provider_id == user.id,
        Appointment.appointment_date > today,
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()

    completed_count = Appointment.query.filter_by(provider_id=user.id, status='Completed').count()
    pending_count = Appointment.query.filter_by(provider_id=user.id, status='Pending').count()

    return render_template(
        'caregiver/dashboard.html',
        user=user,
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments,
        completed_count=completed_count,
        pending_count=pending_count
    )

@caregiver_bp.route('/appointments/<int:appointment_id>/status', methods=['POST'])
@login_required
@role_required('caregiver', 'admin')
def update_status(appointment_id):
    user = get_current_user()
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')

    success, msg = update_appointment_status(appointment_id, new_status, updater=user, reason=notes)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('caregiver.dashboard'))
