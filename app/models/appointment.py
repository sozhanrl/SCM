from datetime import datetime, timezone
import uuid
from app.extensions import db

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='RESTRICT'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='Pending', index=True) # 'Pending', 'Confirmed', 'Completed', 'Cancelled'
    cancellation_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client = db.relationship('User', back_populates='client_appointments', foreign_keys=[user_id])
    provider = db.relationship('User', back_populates='caregiver_appointments', foreign_keys=[provider_id])
    service = db.relationship('Service', back_populates='appointments')

    def __init__(self, **kwargs):
        if 'appointment_code' not in kwargs or not kwargs['appointment_code']:
            today_str = datetime.now().strftime('%Y%m%d')
            rand_suffix = uuid.uuid4().hex[:6].upper()
            kwargs['appointment_code'] = f"APT-{today_str}-{rand_suffix}"
        super().__init__(**kwargs)

    @property
    def is_cancellable(self) -> bool:
        """Determines if the appointment can be cancelled (e.g. if not already completed or cancelled)."""
        return self.status in ('Pending', 'Confirmed')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'appointment_code': self.appointment_code,
            'user_id': self.user_id,
            'client_name': self.client.full_name if self.client else None,
            'client_email': self.client.email if self.client else None,
            'service_id': self.service_id,
            'service_name': self.service.name if self.service else None,
            'service_price': float(self.service.price) if self.service and self.service.price else 0.0,
            'provider_id': self.provider_id,
            'provider_name': self.provider.full_name if self.provider else 'Unassigned',
            'appointment_date': self.appointment_date.strftime('%Y-%m-%d') if self.appointment_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'time_slot': f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}" if self.start_time and self.end_time else None,
            'notes': self.notes,
            'status': self.status,
            'cancellation_reason': self.cancellation_reason,
            'is_cancellable': self.is_cancellable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Appointment {self.appointment_code} ({self.status})>"
