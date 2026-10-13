from datetime import datetime, date, time, timedelta, timezone
from app.extensions import db
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.user import User
from app.services.activity_service import log_activity

DEFAULT_SLOTS = [
    ("08:00", "09:00"),
    ("09:30", "10:30"),
    ("11:00", "12:00"),
    ("13:00", "14:00"),
    ("14:30", "15:30"),
    ("16:00", "17:00"),
    ("17:30", "18:30")
]

def parse_time(time_str: str) -> time:
    if isinstance(time_str, time):
        return time_str
    parts = time_str.strip().split(':')
    return time(int(parts[0]), int(parts[1]))

def get_available_time_slots(date_val: date, provider_id: int = None, service_id: int = None) -> list[dict]:
    """Computes available slots for a given date, checking for existing active bookings."""
    if isinstance(date_val, str):
        date_val = datetime.strptime(date_val, '%Y-%m-%d').date()

    # Active appointments on that date that aren't cancelled
    query = Appointment.query.filter(
        Appointment.appointment_date == date_val,
        Appointment.status.in_(['Pending', 'Confirmed'])
    )
    if provider_id:
        query = query.filter(Appointment.provider_id == provider_id)

    booked_appointments = query.all()
    
    slots_info = []
    for start_str, end_str in DEFAULT_SLOTS:
        s_time = parse_time(start_str)
        e_time = parse_time(end_str)

        # Check conflict
        is_booked = any(
            (app.start_time == s_time or (app.start_time <= s_time < app.end_time))
            for app in booked_appointments
        )

        slots_info.append({
            'start_time': start_str,
            'end_time': end_str,
            'display': f"{datetime.strptime(start_str, '%H:%M').strftime('%I:%M %p')} - {datetime.strptime(end_str, '%H:%M').strftime('%I:%M %p')}",
            'is_available': not is_booked
        })

    return slots_info

def book_appointment(user_id: int, service_id: int, appointment_date_str: str, start_time_str: str, notes: str = None, provider_id: int = None) -> tuple[Appointment | None, list[str]]:
    """Books a new appointment with double-booking prevention and transaction safety."""
    errors = []

    user = db.session.get(User, user_id)
    if not user:
        return None, ["User not found."]

    service = db.session.get(Service, service_id)
    if not service or not service.is_active:
        return None, ["Selected service is invalid or currently inactive."]

    try:
        if isinstance(appointment_date_str, date):
            app_date = appointment_date_str
        else:
            app_date = datetime.strptime(appointment_date_str.strip(), '%Y-%m-%d').date()
    except Exception:
        return None, ["Invalid appointment date format. Use YYYY-MM-DD."]

    today = date.today()
    if app_date < today:
        return None, ["Appointments cannot be booked in the past."]

    try:
        s_time = parse_time(start_time_str)
    except Exception:
        return None, ["Invalid start time format."]

    # Calculate end time based on duration
    duration = service.duration_minutes or 60
    start_dt = datetime.combine(app_date, s_time)
    end_dt = start_dt + timedelta(minutes=duration)
    e_time = end_dt.time()

    # Assign provider: if provider_id not passed, pick an active caregiver or leave unassigned
    assigned_provider_id = None
    if provider_id:
        prov = db.session.get(User, provider_id)
        if prov and prov.is_caregiver and prov.is_active:
            assigned_provider_id = prov.id
    else:
        # Default auto-assignment to first available caregiver without collision
        available_caregivers = User.query.filter_by(role='caregiver', is_active=True).all()
        for cg in available_caregivers:
            conflict = Appointment.query.filter(
                Appointment.provider_id == cg.id,
                Appointment.appointment_date == app_date,
                Appointment.status.in_(['Pending', 'Confirmed']),
                Appointment.start_time == s_time
            ).first()
            if not conflict:
                assigned_provider_id = cg.id
                break

    # Prevent double-booking for the user at the same slot
    user_conflict = Appointment.query.filter(
        Appointment.user_id == user.id,
        Appointment.appointment_date == app_date,
        Appointment.status.in_(['Pending', 'Confirmed']),
        Appointment.start_time == s_time
    ).first()
    if user_conflict:
        return None, [f"You already have a booking ({user_conflict.appointment_code}) scheduled at this date and time."]

    # Prevent double-booking for assigned provider
    if assigned_provider_id:
        prov_conflict = Appointment.query.filter(
            Appointment.provider_id == assigned_provider_id,
            Appointment.appointment_date == app_date,
            Appointment.status.in_(['Pending', 'Confirmed']),
            Appointment.start_time == s_time
        ).first()
        if prov_conflict:
            return None, ["The selected caregiver is already booked for this time slot. Please choose another time or provider."]

    try:
        appointment = Appointment(
            user_id=user.id,
            service_id=service.id,
            provider_id=assigned_provider_id,
            appointment_date=app_date,
            start_time=s_time,
            end_time=e_time,
            notes=notes.strip() if notes else None,
            status='Pending'
        )
        db.session.add(appointment)
        db.session.commit()

        log_activity('APPOINTMENT_BOOKED', user_id=user.id, details=f"Booked appointment {appointment.appointment_code} for {service.name} on {app_date}")
        return appointment, []
    except Exception as e:
        db.session.rollback()
        return None, [f"Failed to book appointment: {str(e)}"]

def cancel_appointment(appointment_id: int, user_id: int = None, is_admin: bool = False, reason: str = None) -> tuple[bool, str]:
    """Cancels an appointment if authorized and not already finished/cancelled."""
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return False, "Appointment not found."

    if not is_admin and appointment.user_id != user_id:
        return False, "You are not authorized to cancel this appointment."

    if not appointment.is_cancellable:
        return False, f"Appointment cannot be cancelled because its current status is '{appointment.status}'."

    try:
        appointment.status = 'Cancelled'
        appointment.cancellation_reason = reason or "Cancelled by user"
        db.session.commit()
        log_activity('APPOINTMENT_CANCELLED', user_id=user_id or appointment.user_id, details=f"Cancelled appointment {appointment.appointment_code}")
        return True, "Appointment has been successfully cancelled."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to cancel appointment: {str(e)}"

def update_appointment_status(appointment_id: int, new_status: str, updater: User, reason: str = None, provider_id: int = None) -> tuple[bool, str]:
    """Updates appointment status and/or caregiver assignment."""
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return False, "Appointment not found."

    valid_statuses = ('Pending', 'Confirmed', 'Completed', 'Cancelled')
    if new_status not in valid_statuses:
        return False, f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}."

    # Caregivers can only update their assigned appointments
    if updater.is_caregiver:
        if appointment.provider_id != updater.id:
            return False, "You can only update appointments assigned to you."

    try:
        appointment.status = new_status
        if reason:
            appointment.cancellation_reason = reason

        # Admin can reassign provider
        if updater.is_admin and provider_id is not None:
            if provider_id == 0:
                appointment.provider_id = None
            else:
                prov = db.session.get(User, provider_id)
                if prov and prov.is_caregiver:
                    appointment.provider_id = prov.id

        db.session.commit()
        log_activity('APPOINTMENT_STATUS_UPDATED', user_id=updater.id, details=f"Appointment {appointment.appointment_code} changed to {new_status}")
        return True, f"Appointment status updated to '{new_status}'."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to update appointment: {str(e)}"
