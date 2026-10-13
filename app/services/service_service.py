from decimal import Decimal
from app.extensions import db
from app.models.service import Service
from app.models.appointment import Appointment
from app.services.activity_service import log_activity

CATEGORIES = [
    'Daily Living Assistance',
    'Medical Support & Nursing',
    'Dementia & Memory Care',
    'Physical Therapy & Rehab',
    'Companionship & Social',
    'Nutrition & Meal Prep',
    'Overnight & Respite Care'
]

def get_services(search: str = None, category: str = None, active_only: bool = False):
    query = Service.query
    if active_only:
        query = query.filter_by(is_active=True)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Service.name.ilike(s)) | (Service.description.ilike(s)) | (Service.service_code.ilike(s)))
    if category and category != 'all':
        query = query.filter_by(category=category)
    return query.order_by(Service.category, Service.name).all()

def get_service_by_id(service_id: int) -> Service | None:
    return Service.query.get(service_id)

def get_service_by_code(service_code: str) -> Service | None:
    return Service.query.filter_by(service_code=service_code).first()

def create_service(data: dict, admin_id: int) -> tuple[Service | None, list[str]]:
    errors = []
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    price = data.get('price', 0)
    duration = data.get('duration_minutes', 60)
    image_path = data.get('image_path', '').strip() or None
    is_active = data.get('is_active', True)

    if not name:
        errors.append("Service name is required.")
    if not description:
        errors.append("Service description is required.")
    if not category:
        errors.append("Category is required.")

    try:
        price_dec = Decimal(str(price))
        if price_dec < 0:
            errors.append("Price cannot be negative.")
    except Exception:
        errors.append("Invalid price format.")
        price_dec = Decimal('0.00')

    try:
        duration_int = int(duration)
        if duration_int <= 0:
            errors.append("Duration must be a positive integer in minutes.")
    except Exception:
        errors.append("Invalid duration.")
        duration_int = 60

    if errors:
        return None, errors

    try:
        service = Service(
            name=name,
            description=description,
            category=category,
            price=price_dec,
            duration_minutes=duration_int,
            image_path=image_path,
            is_active=bool(is_active)
        )
        db.session.add(service)
        db.session.commit()
        log_activity('SERVICE_CREATED', user_id=admin_id, details=f"Created service {service.name} ({service.service_code})")
        return service, []
    except Exception as e:
        db.session.rollback()
        return None, [f"Failed to create service: {str(e)}"]

def update_service(service_id: int, data: dict, admin_id: int) -> tuple[Service | None, list[str]]:
    service = db.session.get(Service, service_id)
    if not service:
        return None, ["Service not found."]

    errors = []
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()

    if not name:
        errors.append("Service name is required.")
    if not description:
        errors.append("Service description is required.")
    if not category:
        errors.append("Category is required.")

    if 'price' in data:
        try:
            price_dec = Decimal(str(data['price']))
            if price_dec < 0:
                errors.append("Price cannot be negative.")
            else:
                service.price = price_dec
        except Exception:
            errors.append("Invalid price format.")

    if 'duration_minutes' in data:
        try:
            dur = int(data['duration_minutes'])
            if dur <= 0:
                errors.append("Duration must be positive.")
            else:
                service.duration_minutes = dur
        except Exception:
            errors.append("Invalid duration.")

    if errors:
        return None, errors

    try:
        service.name = name
        service.description = description
        service.category = category
        if 'image_path' in data:
            service.image_path = data['image_path'].strip() or None
        if 'is_active' in data:
            service.is_active = bool(data['is_active'])

        db.session.commit()
        log_activity('SERVICE_UPDATED', user_id=admin_id, details=f"Updated service {service.name} ({service.service_code})")
        return service, []
    except Exception as e:
        db.session.rollback()
        return None, [f"Failed to update service: {str(e)}"]

def delete_service(service_id: int, admin_id: int) -> tuple[bool, str]:
    """Deletes a service or protects it if appointment history exists."""
    service = db.session.get(Service, service_id)
    if not service:
        return False, "Service not found."

    # Prevent accidental loss of appointment-related data
    appointment_count = Appointment.query.filter_by(service_id=service.id).count()
    if appointment_count > 0:
        return False, f"Cannot delete service '{service.name}' because {appointment_count} appointment records are associated with it. You can deactivate it instead to hide it from new bookings."

    try:
        name = service.name
        code = service.service_code
        db.session.delete(service)
        db.session.commit()
        log_activity('SERVICE_DELETED', user_id=admin_id, details=f"Deleted service {name} ({code})")
        return True, f"Service '{name}' has been successfully deleted."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to delete service: {str(e)}"
