from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user', index=True)  # 'admin', 'user', 'caregiver'
    profile_image = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client_appointments = db.relationship('Appointment', back_populates='client', foreign_keys='Appointment.user_id', cascade='all, delete-orphan', lazy='dynamic')
    caregiver_appointments = db.relationship('Appointment', back_populates='provider', foreign_keys='Appointment.provider_id', lazy='dynamic')
    reset_tokens = db.relationship('PasswordResetToken', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    verification_tokens = db.relationship('EmailVerificationToken', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy='dynamic')

    def __init__(self, **kwargs):
        if 'user_code' not in kwargs or not kwargs['user_code']:
            kwargs['user_code'] = f"USR-{uuid.uuid4().hex[:8].upper()}"
        super().__init__(**kwargs)

    def set_password(self, password: str):
        """Hashes password with Werkzeug security generate_password_hash (scrypt/pbkdf2)."""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies password using Werkzeug check_password_hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    @property
    def is_caregiver(self) -> bool:
        return self.role == 'caregiver'

    @property
    def is_client(self) -> bool:
        return self.role == 'user'

    def get_avatar_url(self) -> str:
        """Returns the profile image URL or default avatar."""
        if self.profile_image:
            return f"/uploads/profiles/{self.profile_image}"
        return "/static/images/default-avatar.svg"

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            'id': self.id,
            'user_code': self.user_code,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'role': self.role,
            'profile_image': self.profile_image,
            'avatar_url': self.get_avatar_url(),
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data

    def __repr__(self):
        return f"<User {self.user_code} - {self.email} ({self.role})>"
