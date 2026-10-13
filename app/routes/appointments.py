from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date
from app.utils.decorators import login_required, get_current_user
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.user import User
from app.services.appointment_service import book_appointment, cancel_appointment, get_available_time_slots

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book():
    user = get_current_user()
    service_id = request.args.get('service_id', type=int)
    services = Service.query.filter_by(is_active=True).all()
    caregivers = User.query.filter_by(role='caregiver', is_active=True).all()
    selected_service = Service.query.get(service_id) if service_id else None

    if request.method == 'POST':
        srv_id = request.form.get('service_id', type=int)
        app_date = request.form.get('appointment_date')
        time_slot = request.form.get('time_slot') # Format "09:30"
        provider_id = request.form.get('provider_id', type=int)
        notes = request.form.get('notes', '')

        if not srv_id or not app_date or not time_slot:
            flash('Please select a service, appointment date, and time slot.', 'danger')
            return render_template(
                'user/book_appointment.html',
                services=services,
                caregivers=caregivers,
                selected_service=selected_service,
                today=date.today().isoformat()
            )

        appointment, errors = book_appointment(
            user_id=user.id,
            service_id=srv_id,
            appointment_date_str=app_date,
            start_time_str=time_slot,
            notes=notes,
            provider_id=provider_id if provider_id and provider_id > 0 else None
        )

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'user/book_appointment.html',
                services=services,
                caregivers=caregivers,
                selected_service=selected_service,
                today=date.today().isoformat()
            )

        flash(f'Appointment booked successfully! Reference ID: {appointment.appointment_code}', 'success')
        return redirect(url_for('appointments.confirmation', appointment_id=appointment.id))

    return render_template(
        'user/book_appointment.html',
        services=services,
        caregivers=caregivers,
        selected_service=selected_service,
        today=date.today().isoformat()
    )

@appointments_bp.route('/appointments/confirmation/<int:appointment_id>')
@login_required
def confirmation(appointment_id):
    user = get_current_user()
    appointment = Appointment.query.get_or_404(appointment_id)

    if not user.is_admin and appointment.user_id != user.id:
        flash('You do not have permission to view that confirmation.', 'danger')
        return redirect(url_for('user.dashboard'))

    return render_template('user/appointment_confirmation.html', appointment=appointment)

@appointments_bp.route('/appointments/my')
@login_required
def my_appointments():
    user = get_current_user()
    appointments = Appointment.query.filter(
        Appointment.user_id == user.id,
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()
    return render_template('user/my_appointments.html', appointments=appointments)

@appointments_bp.route('/appointments/history')
@login_required
def history():
    user = get_current_user()
    appointments = Appointment.query.filter(
        Appointment.user_id == user.id
    ).order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()).all()
    return render_template('user/appointment_history.html', appointments=appointments)

@appointments_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Cancelled by client')
    success, msg = cancel_appointment(appointment_id, user_id=user.id, is_admin=user.is_admin, reason=reason)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    if user.is_admin:
        return redirect(url_for('admin.appointments'))
    return redirect(url_for('appointments.my_appointments'))
