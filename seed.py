import os
from datetime import datetime, date, time, timedelta, timezone
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.cms import Page, Media
from app.models.activity import ActivityLog

app = create_app(os.getenv('FLASK_ENV', 'development'))

def seed_database():
    with app.app_context():
        print("Ensuring database tables exist...")
        db.create_all()

        # 1. Seed Administrator
        admin = User.query.filter_by(email='admin@eldencare.com').first()
        if not admin:
            admin = User(
                user_code='USR-ADMIN001',
                full_name='System Administrator',
                email='admin@eldencare.com',
                phone='+1 (555) 019-2834',
                address='100 Elden Healthcare Blvd, Suite 400, Boston, MA',
                role='admin',
                is_active=True,
                email_verified=True
            )
            admin.set_password('Admin@123456')
            db.session.add(admin)
            print("Created Admin user: admin@eldencare.com / Admin@123456")
        else:
            print("Admin user already exists.")

        # 2. Seed Caregivers
        caregivers_data = [
            {
                'code': 'USR-CG001',
                'name': 'Sarah Johnson, RN',
                'email': 'sarah.johnson@eldencare.com',
                'phone': '+1 (555) 019-7721',
                'address': '24 Beacon Hill Way, Boston, MA',
                'password': 'Caregiver@123'
            },
            {
                'code': 'USR-CG002',
                'name': 'David Miller, PT',
                'email': 'david.miller@eldencare.com',
                'phone': '+1 (555) 019-3382',
                'address': '89 Cambridge St, Cambridge, MA',
                'password': 'Caregiver@123'
            },
            {
                'code': 'USR-CG003',
                'name': 'Maria Garcia, CNA',
                'email': 'maria.garcia@eldencare.com',
                'phone': '+1 (555) 019-9943',
                'address': '15 Harvard Ave, Brookline, MA',
                'password': 'Caregiver@123'
            }
        ]
        created_caregivers = []
        for cg in caregivers_data:
            existing = User.query.filter_by(email=cg['email']).first()
            if not existing:
                u = User(
                    user_code=cg['code'],
                    full_name=cg['name'],
                    email=cg['email'],
                    phone=cg['phone'],
                    address=cg['address'],
                    role='caregiver',
                    is_active=True,
                    email_verified=True
                )
                u.set_password(cg['password'])
                db.session.add(u)
                created_caregivers.append(u)
                print(f"Created Caregiver: {cg['email']} / {cg['password']}")
            else:
                created_caregivers.append(existing)

        # 3. Seed Care Recipients (Clients)
        clients_data = [
            {
                'code': 'USR-REC001',
                'name': 'Eleanor Vance',
                'email': 'eleanor.vance@example.com',
                'phone': '+1 (555) 012-3456',
                'address': '42 Magnolia Gardens, Apt 3B, Boston, MA',
                'password': 'User@123456'
            },
            {
                'code': 'USR-REC002',
                'name': 'Arthur Pendleton',
                'email': 'arthur.pendleton@example.com',
                'phone': '+1 (555) 012-9876',
                'address': '18 Heritage Oaks Lane, Somerville, MA',
                'password': 'User@123456'
            }
        ]
        created_clients = []
        for c in clients_data:
            existing = User.query.filter_by(email=c['email']).first()
            if not existing:
                u = User(
                    user_code=c['code'],
                    full_name=c['name'],
                    email=c['email'],
                    phone=c['phone'],
                    address=c['address'],
                    role='user',
                    is_active=True,
                    email_verified=True
                )
                u.set_password(c['password'])
                db.session.add(u)
                created_clients.append(u)
                print(f"Created Client: {c['email']} / {c['password']}")
            else:
                created_clients.append(existing)

        db.session.commit()

        # 4. Seed Services
        services_data = [
            {
                'code': 'SVC-001',
                'name': 'Personal Daily Living Assistance',
                'category': 'Daily Living Assistance',
                'price': 350.00,
                'duration': 60,
                'desc': 'Compassionate assistance with daily personal routines including bathing, dressing, grooming, and mobility support designed for dignity and comfort.'
            },
            {
                'code': 'SVC-002',
                'name': 'Skilled Nursing & Medication Management',
                'category': 'Medical Support & Nursing',
                'price': 650.00,
                'duration': 60,
                'desc': 'Professional clinical care by licensed nurses. Includes medication administration, vital signs tracking, wound dressing, and physician coordination.'
            },
            {
                'code': 'SVC-003',
                'name': 'Dementia & Memory Care Therapy',
                'category': 'Dementia & Memory Care',
                'price': 480.00,
                'duration': 60,
                'desc': 'Specialized support for seniors living with Alzheimer’s or dementia. Cognitive stimulation games, gentle memory therapy, and safety oversight.'
            },
            {
                'code': 'SVC-004',
                'name': 'Physical Rehabilitation & Mobility Exercises',
                'category': 'Physical Therapy & Rehab',
                'price': 550.00,
                'duration': 60,
                'desc': 'Tailored light exercises and physical therapy sessions to restore balance, enhance flexibility, and prevent fall injuries.'
            },
            {
                'code': 'SVC-005',
                'name': 'Companionship & Social Engagement',
                'category': 'Companionship & Social',
                'price': 280.00,
                'duration': 60,
                'desc': 'Friendly companion visits featuring active conversation, reading, board games, guided garden walks, and community connection.'
            },
            {
                'code': 'SVC-006',
                'name': 'Nutritious Meal Prep & Dietary Management',
                'category': 'Nutrition & Meal Prep',
                'price': 320.00,
                'duration': 60,
                'desc': 'Home-cooked healthy meals tailored to senior dietary requirements, diabetic menus, low-sodium regimens, and hydration tracking.'
            },
            {
                'code': 'SVC-007',
                'name': 'Overnight Monitoring & Respite Care',
                'category': 'Overnight & Respite Care',
                'price': 850.00,
                'duration': 120,
                'desc': 'Attentive overnight presence providing peace of mind, nighttime transfers, medication reminders, and respite for family caregivers.'
            }
        ]

        created_services = []
        for s in services_data:
            existing = Service.query.filter_by(service_code=s['code']).first()
            if not existing:
                svc = Service(
                    service_code=s['code'],
                    name=s['name'],
                    category=s['category'],
                    price=s['price'],
                    duration_minutes=s['duration'],
                    description=s['desc'],
                    is_active=True
                )
                db.session.add(svc)
                created_services.append(svc)
                print(f"Created Service: {s['name']}")
            else:
                created_services.append(existing)

        db.session.commit()

        # 5. Seed CMS Pages
        pages_data = [
            {
                'slug': 'home',
                'title': 'Compassionate Senior Care at Home',
                'meta': 'Dedicated elder care services promoting independence, safety, and joy at home.',
                'content': '<p>Welcome to <strong>Elden Care</strong>. We believe every senior deserves to age with respect, dignity, and personalized comfort. Our licensed healthcare specialists and dedicated caregivers support your loved ones 24/7.</p>'
            },
            {
                'slug': 'about',
                'title': 'About Elden Care',
                'meta': 'Learn more about our mission, heritage, and certified caregiving staff.',
                'content': '<p>Founded with a heart for community wellness, Elden Care has been a trusted beacon for elder care since 2018. We combine healthcare expertise with heartfelt companionship to empower seniors to live happily in their cherished homes.</p>'
            },
            {
                'slug': 'contact',
                'title': 'Contact Our Care Advisors',
                'meta': 'Get in touch with Elden Care coordinators for personalized care consultations.',
                'content': '<p>Have questions or need emergency assistance? Our team is available 24 hours a day, 7 days a week.</p><p><strong>Call Us:</strong> +1 (800) 555-ELDEN<br><strong>Email:</strong> support@eldencare.com</p>'
            },
            {
                'slug': 'faq',
                'title': 'Frequently Asked Questions',
                'meta': 'Answers to common questions about senior care services, booking, and caregiver matching.',
                'content': '<h3>How do you match caregivers?</h3><p>We match caregivers based on specific medical requirements, personality compatibility, and scheduling needs.</p><h3>Can I reschedule or cancel?</h3><p>Yes, appointments can be easily managed directly from your user dashboard.</p>'
            }
        ]

        for p in pages_data:
            existing = Page.query.filter_by(slug=p['slug']).first()
            if not existing:
                pg = Page(
                    slug=p['slug'],
                    title=p['title'],
                    meta_description=p['meta'],
                    content=p['content'],
                    status='published',
                    created_by=admin.id if admin else None
                )
                db.session.add(pg)
                print(f"Created CMS Page: {p['slug']}")

        db.session.commit()

        # 6. Seed Sample Appointments
        if created_clients and created_services and created_caregivers:
            client1 = created_clients[0]
            cg1 = created_caregivers[0]
            svc1 = created_services[0]

            existing_app = Appointment.query.filter_by(user_id=client1.id).first()
            if not existing_app:
                tomorrow = date.today() + timedelta(days=1)
                app1 = Appointment(
                    appointment_code='APT-20261014-SAMPLE1',
                    user_id=client1.id,
                    service_id=svc1.id,
                    provider_id=cg1.id,
                    appointment_date=tomorrow,
                    start_time=time(9, 30),
                    end_time=time(10, 30),
                    notes='Assistance with morning routines and gentle stretching exercises.',
                    status='Confirmed'
                )
                db.session.add(app1)

                app2 = Appointment(
                    appointment_code='APT-20261015-SAMPLE2',
                    user_id=created_clients[1].id,
                    service_id=created_services[1].id,
                    provider_id=created_caregivers[1].id,
                    appointment_date=tomorrow + timedelta(days=1),
                    start_time=time(11, 0),
                    end_time=time(12, 0),
                    notes='Blood pressure check and insulin regimen review.',
                    status='Pending'
                )
                db.session.add(app2)

                print("Created sample appointments.")
                db.session.commit()

        # 7. Initial Activity Log
        log = ActivityLog(
            user_id=admin.id if admin else None,
            action='DATABASE_SEEDED',
            details='Initial administrative and demonstration dataset created.'
        )
        db.session.add(log)
        db.session.commit()

        print("\n=======================================================")
        print("SEEDING COMPLETE!")
        print("Administrative Account:")
        print("  Email:    admin@eldencare.com")
        print("  Password: Admin@123456")
        print("\nCaregiver Account:")
        print("  Email:    sarah.johnson@eldencare.com")
        print("  Password: Caregiver@123")
        print("\nCare Recipient (Client) Account:")
        print("  Email:    eleanor.vance@example.com")
        print("  Password: User@123456")
        print("=======================================================\n")

if __name__ == '__main__':
    seed_database()
