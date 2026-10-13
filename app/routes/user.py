from flask import Blueprint, render_template, redirect, url_for
from app.utils.decorators import login_required, role_required, get_current_user
from app.models.appointment import Appointment
from app.models.service import Service

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
@role_required('user')
def dashboard():
    user = get_current_user()
    active_appointments = Appointment.query.filter(
        Appointment.user_id == user.id,
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()

    past_appointments = Appointment.query.filter(
        Appointment.user_id == user.id,
        Appointment.status.in_(['Completed', 'Cancelled'])
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()

    recommended_services = Service.query.filter_by(is_active=True).limit(3).all()

    return render_template(
        'user/dashboard.html',
        user=user,
        active_appointments=active_appointments,
        past_appointments=past_appointments,
        recommended_services=recommended_services
    )
