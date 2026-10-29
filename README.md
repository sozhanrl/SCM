# Elden Care – Elder Care Website Management System

[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/Flask-3.1%2B-green.svg)](https://palletsprojects.com/p/flask/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-teal.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-29%20Passing-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-Proprietary-slate.svg)](#)

A secure, accessible, full-stack web application designed for elder care service management, appointment booking, caregiver scheduling, and website content management. Built specifically with accessible UI components, high-contrast healthcare palettes, and large typography suitable for elderly individuals, family members, caregivers, and administrative staff.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [Azure DevOps Work-Item Mapping](#4-azure-devops-work-item-mapping)
5. [Database Architecture & Schema](#5-database-architecture--schema)
6. [Installation & Setup](#6-installation--setup)
7. [Database Setup (MySQL & SQLite)](#7-database-setup-mysql--sqlite)
8. [Demonstration Credentials](#8-demonstration-credentials)
9. [RESTful API Reference](#9-restful-api-reference)
10. [Automated Testing](#10-automated-testing)
11. [Security & Accessibility Features](#11-security--accessibility-features)
12. [Project Directory Structure](#12-project-directory-structure)

---

## 1. Project Overview

**Elden Care** provides an end-to-end management platform for non-profit and commercial elder care organizations. The platform handles:
- **Client & Caregiver Accounts:** Secure onboarding with unique identifiers (`USR-XXXXXX`), profile image management, and password reset workflows.
- **Service Catalog:** Dynamic healthcare offerings including Daily Living Assistance, Skilled Nursing, Dementia & Memory Care, Physical Therapy, and Companion Visits.
- **Smart Appointment Booking:** Conflict-free scheduling with dynamic slot generation, client and caregiver collision prevention, and instant confirmation receipts.
- **Caregiver Dispatch:** A dedicated portal for licensed nurses and home health aides to review visits, access client directions, and record care milestones.
- **Content Management System (CMS):** In-app page editor and media library allowing administrators to manage website pages and marketing assets without code deployments.

---

## 2. Technology Stack

- **Backend Framework:** Python 3.12+ / Flask with modular Blueprints
- **Database Access & ORM:** SQLAlchemy with Flask-SQLAlchemy 3.1+
- **Database Engines:** MySQL 8.0+ (Production target via `PyMySQL`) with seamless local SQLite fallback
- **Authentication & Security:** Flask session management, Werkzeug password hashing (`generate_password_hash` / `check_password_hash`), Flask-WTF CSRF protection
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons, Google Fonts (Inter & Outfit)
- **API Testing:** Postman & pytest test clients
- **Test Framework:** Pytest 9.1+ with in-memory test database isolation

---

## 3. User Roles & Permissions

| Role | Access Level | Permitted Actions |
| :--- | :--- | :--- |
| **Administrator** | Full System Access | Manage all users, toggle accounts, add/edit/delete services, manage all bookings, reassign caregivers, publish CMS pages, upload media, inspect audit logs. |
| **Care Recipient / Client** | Client Portal | Book care appointments, view upcoming visits, cancel eligible bookings, view past history, edit profile details, upload profile image, change password. |
| **Caregiver / Provider** | Caregiver Portal | View assigned visits for today and upcoming dates, access client contact/address, update visit status (`Confirmed`, `Completed`, `Cancelled`), edit own profile. |

*Permissions are strictly enforced on the server-side via `@login_required`, `@role_required`, and `@admin_required` decorators, preventing unauthorized URL or API manipulation.*

---

## 4. Azure DevOps Work-Item Mapping

The project maps directly to the Azure DevOps delivery backlog:

| Phase | Azure DevOps Backlog Items | Status |
| :--- | :--- | :--- |
| **Phase 1: Foundation** | Elden Care Website Management System, Database setup, User Authentication | Complete |
| **Phase 2: Registration & Login** | User Registration, Registration validation, Registration API, Login UI, Login authentication, Database integration | Complete |
| **Phase 3: Password Management** | Password Management, Create Reset Password Page, Email Verification, Validate Old and New Password, Password Not Updating | Complete |
| **Phase 4: Profile Management** | Profile Management, View Profile, Edit Profile, Upload Profile Image, Fetch User Data, Profile Update Error | Complete |
| **Phase 5: Admin & Services** | Admin Dashboard, View All Users, Manage Users, Service Management, Add Service, Edit Service, Delete Service | Complete |
| **Phase 6: Appointments** | Appointment Booking, Book Appointment, Cancel Appointment, Prevent Double Booking | Complete |
| **Phase 7: CMS** | Manage Pages, Manage Images, Update Website Content | Complete |
| **Phase 8: Testing & Deployment** | Integration testing, Security testing, Responsive UI testing, Documentation | Complete |

---

## 5. Database Architecture & Schema

The database schema is fully normalized into 8 tables:

1. `users`: Stores user profiles, authentication hashes, contact numbers, roles (`admin`, `user`, `caregiver`), and generated codes (`USR-XXXXXX`).
2. `services`: Catalog of elder care offerings, categories, durations, hourly prices, and active flags.
3. `appointments`: Care bookings linking client, service, and assigned caregiver with unique codes (`APT-YYYYMMDD-XXXXXX`), date, start/end times, notes, and statuses.
4. `pages`: CMS dynamic pages with slug, title, rich HTML content, meta descriptions, and publish status.
5. `media`: Uploaded assets, file paths, MIME types, file sizes, captions, and uploader attribution.
6. `password_reset_tokens`: Single-use SHA-256 hashed tokens with timestamp-based expiration.
7. `email_verification_tokens`: Account email verification records.
8. `activity_logs`: Audit logs capturing logins, account changes, booking creation, cancellations, and IP addresses.

*The raw DDL is available in [schema.sql](schema.sql) for direct MySQL execution.*

---

## 6. Installation & Setup

### Prerequisites
- Python 3.12 or newer installed on your system
- Git command-line tools
- (Optional) MySQL Server 8.0+ or MariaDB 10.5+

### Step-by-Step Installation

1. **Clone or open the repository:**
   ```bash
   cd e:\SCM
   ```

2. **Activate the Python Virtual Environment:**
   - **Windows:**
     ```powershell
     .venv\Scripts\activate
     ```
   - **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Review `.env` (or copy from `.env.example`):
   ```ini
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=elden-care-super-secret-development-key-2026
   DATABASE_URL=sqlite:///instance/elden_care.db
   UPLOAD_FOLDER=uploads
   ```

---

## 7. Database Setup (MySQL & SQLite)

### Option A: Using Local SQLite (Immediate Out-of-the-Box Development)
The repository includes an automatic SQLite configuration so you can start developing instantly without configuring a database server:
```bash
python init_db.py
```
This initializes the database schema and seeds administrative, caregiver, client, and service records.

### Option B: Connecting to MySQL
1. Ensure your local or remote MySQL server is running.
2. Create the database:
   ```sql
   CREATE DATABASE elden_care CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Update your `.env` file with your MySQL credentials:
   ```ini
   DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:3306/elden_care
   ```
4. Run the initialization and seeding script:
   ```bash
   python init_db.py
   ```
   *Alternatively, import the raw DDL schema directly:*
   ```bash
   mysql -u root -p elden_care < schema.sql
   python seed.py
   ```

---

## 8. Demonstration Credentials

The database seeder provisions pre-configured test accounts:

| Role | Email Address | Password | User Identifier |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@eldencare.com` | `Admin@123456` | `USR-ADMIN001` |
| **Caregiver (RN)** | `sarah.johnson@eldencare.com` | `Caregiver@123` | `USR-CG001` |
| **Caregiver (PT)** | `david.miller@eldencare.com` | `Caregiver@123` | `USR-CG002` |
| **Care Recipient (Client)** | `eleanor.vance@example.com` | `User@123456` | `USR-REC001` |
| **Care Recipient (Client)** | `arthur.pendleton@example.com` | `User@123456` | `USR-REC002` |

---

## 9. RESTful API Reference

All API routes return structured JSON responses with `success`, `message`, and optional `data`.

### Authentication Endpoints
- `POST /api/auth/register`: Register new client or caregiver account.
- `POST /api/auth/login`: Authenticate user and initiate session cookie.
- `POST /api/auth/logout`: Destroy active session.
- `POST /api/auth/change-password`: Update password (requires login).
- `POST /api/auth/forgot-password`: Generate single-use reset token.
- `POST /api/auth/reset-password`: Set new password with valid token.

### Profile Endpoints
- `GET /api/profile`: Retrieve authenticated user profile.
- `PUT /api/profile`: Update contact number, address, and name.
- `POST /api/profile/image`: Upload profile picture (JPEG/PNG/WebP, max 5MB).

### Service Endpoints
- `GET /api/services`: List available services (supports `search` and `category` query params).
- `POST /api/admin/services`: Create new service (Admin only).
- `PUT /api/admin/services/<id>`: Modify existing service (Admin only).
- `DELETE /api/admin/services/<id>`: Delete service with appointment protection check (Admin only).

### Appointment Endpoints
- `GET /api/appointments/available-slots`: Retrieve available time slots for a given date and provider.
- `GET /api/appointments`: List user's, caregiver's, or all appointments.
- `POST /api/appointments`: Book an appointment (enforces collision prevention).
- `GET /api/appointments/<id>`: Get appointment details.
- `PATCH /api/appointments/<id>/cancel`: Cancel appointment with reason.
- `PATCH /api/admin/appointments/<id>/status`: Update appointment status or reassign caregiver.

### CMS Endpoints
- `GET /api/pages`: List published CMS pages.
- `POST /api/admin/pages`: Create page (Admin only).
- `PUT /api/admin/pages/<id>`: Update page content or slug (Admin only).
- `DELETE /api/admin/pages/<id>`: Delete page (protects core pages: home, about, services, contact).
- `GET /api/admin/media`: List uploaded media files.
- `POST /api/admin/media`: Upload media image.
- `DELETE /api/admin/media/<id>`: Remove media asset.

---

## 10. Automated Testing

The project contains a comprehensive automated test suite built with `pytest`:

```bash
# Run all tests
python -m pytest

# Run with verbose output and coverage summary
python -m pytest -v
```

### Covered Test Scenarios:
- **Authentication:** Successful registration, duplicate email rejection, role assignment restrictions, valid/invalid password verification, unauthorized dashboard redirection.
- **Password Management:** Authenticated password changes, reset token expiration, single-use token consumption.
- **Profile:** Details retrieval, updating contact fields, valid avatar upload, invalid file extension rejection.
- **Services:** Creation, updates, deletions, authorization checks, and appointment relationship protection.
- **Appointments:** Conflict-free booking, double-booking prevention for overlapping slots, cancellations, caregiver status transitions.
- **CMS & Media:** Page publication, slug conflict handling, core page deletion protection, file asset management.

---

## 11. Security & Accessibility Features

### Senior-Friendly Accessibility
- **Large Typography & Text Sizing:** Dedicated font size scale buttons (`Normal`, `Large`, `A+`) saved in browser `localStorage`.
- **High-Contrast Healthcare Palette:** Deep navy blue (`#1e3a8a`), slate darks (`#0f172a`), and clear white cards ensuring compliance with contrast guidelines.
- **Simplified Booking:** Dynamic slot selection pills instead of ambiguous manual text inputs.
- **24/7 Telephone Hotline:** Prominently featured emergency dispatch bar across all views.

### Security Architecture
- **Password Security:** Scrypt/PBKDF2 salted password hashing via Werkzeug; plain-text passwords are never stored.
- **Cross-Site Request Forgery (CSRF):** Enabled on all cookie-authenticated HTML forms via `Flask-WTF`.
- **Session Protection:** `HttpOnly`, `SameSite=Lax` cookies with session regeneration on role changes.
- **File Upload Hardening:** Extension whitelisting (`png`, `jpg`, `jpeg`, `webp`, `gif`), content-length limits (16 MB max), unique random file naming, and path traversal protection.
- **SQL Injection Prevention:** Parameterized database queries handled through SQLAlchemy ORM.

---

## 12. Project Directory Structure

```text
elden-care/
├── app/
│   ├── __init__.py               # Flask application factory & error handlers
│   ├── config.py                 # Configuration loader & environment binding
│   ├── extensions.py             # SQLAlchemy & CSRF instances
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── user.py               # User account & password hashing
│   │   ├── service.py            # Elder care service catalog
│   │   ├── appointment.py        # Booking schedules & statuses
│   │   ├── cms.py                # CMS Page & Media models
│   │   ├── token.py              # Password reset & verification tokens
│   │   └── activity.py           # System audit logging
│   ├── routes/                   # Route controllers & API blueprints
│   │   ├── __init__.py
│   │   ├── public.py             # Public website (Home, About, Services, Contact)
│   │   ├── auth.py               # Registration, Login, Logout, Password Resets
│   │   ├── profile.py            # User profile viewing & image upload
│   │   ├── user.py               # Client dashboard & appointments
│   │   ├── caregiver.py          # Caregiver dispatch portal
│   │   ├── appointments.py       # Appointment booking & cancellation
│   │   ├── admin.py              # Administration management & CMS views
│   │   └── api.py                # RESTful JSON APIs
│   ├── services/                 # Business logic & services
│   │   ├── activity_service.py   # Security auditing
│   │   ├── auth_service.py       # Authentication & token generation
│   │   ├── appointment_service.py# Booking logic & collision prevention
│   │   ├── user_service.py       # User management
│   │   ├── service_service.py    # Service catalog logic
│   │   └── cms_service.py        # CMS page & media management
│   ├── static/
│   │   ├── css/style.css         # Healthcare design system & accessibility tokens
│   │   ├── js/main.js            # Slot loader, image previews, alert dismissals
│   │   └── images/               # SVG placeholders & assets
│   └── templates/                # Responsive Jinja2 templates
│       ├── base.html             # Master layout with hotline & accessibility bar
│       ├── public/               # Public pages (home, about, services, contact, error)
│       ├── auth/                 # Login, register, forgot/reset password
│       ├── user/                 # Client dashboard, profile, booking, history
│       ├── caregiver/            # Caregiver portal & visit status updates
│       └── admin/                # Admin overview, users, services, CMS, media, logs
├── instance/                     # Local SQLite database directory (ignored by git)
├── uploads/                      # Upload directories for profiles and media
├── tests/                        # Pytest automated test suite (29 tests)
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_profile.py
│   ├── test_services.py
│   ├── test_appointments.py
│   ├── test_admin.py
│   └── test_cms.py
├── .env                          # Local environment variables
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file
├── config.py                     # Root configuration module
├── init_db.py                    # Database schema creation & seeding runner
├── requirements.txt              # Pinned Python package dependencies
├── run.py                        # Application entry point
├── schema.sql                    # Normalized MySQL DDL schema
└── seed.py                       # Sample data & initial administrator account seeder
```

---

## 13. Running the Application

To start the development server:

```powershell
.venv\Scripts\python.exe run.py
```

The application will be live at:
- **Public Website:** `http://localhost:5000/`
- **Login Portal:** `http://localhost:5000/login`
- **Admin Dashboard:** `http://localhost:5000/admin/dashboard`
- **Caregiver Portal:** `http://localhost:5000/caregiver/dashboard`
- **REST API Endpoints:** `http://localhost:5000/api/...`
