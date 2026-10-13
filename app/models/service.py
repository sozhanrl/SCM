from datetime import datetime, timezone
import uuid
from app.extensions import db

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    service_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    image_path = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    appointments = db.relationship('Appointment', back_populates='service', lazy='dynamic')

    def __init__(self, **kwargs):
        if 'service_code' not in kwargs or not kwargs['service_code']:
            kwargs['service_code'] = f"SVC-{uuid.uuid4().hex[:6].upper()}"
        super().__init__(**kwargs)

    def get_image_url(self) -> str:
        if self.image_path:
            if self.image_path.startswith('http') or self.image_path.startswith('/'):
                return self.image_path
            return f"/uploads/media/{self.image_path}"
        return "/static/images/service-default.svg"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'service_code': self.service_code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'price': float(self.price) if self.price is not None else 0.0,
            'duration_minutes': self.duration_minutes,
            'image_path': self.image_path,
            'image_url': self.get_image_url(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Service {self.service_code} - {self.name}>"
