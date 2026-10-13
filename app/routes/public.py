from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.service import Service
from app.models.cms import Page
from app.models.user import User
from app.utils.decorators import get_current_user

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    services = Service.query.filter_by(is_active=True).limit(6).all()
    # Check if a CMS custom homepage exists
    cms_home = Page.query.filter_by(slug='home', status='published').first()
    caregivers_count = User.query.filter_by(role='caregiver', is_active=True).count()
    users_count = User.query.filter_by(role='user', is_active=True).count()
    return render_template('public/home.html', services=services, cms_home=cms_home, caregivers_count=caregivers_count, users_count=users_count)

@public_bp.route('/about')
def about():
    cms_about = Page.query.filter_by(slug='about', status='published').first()
    caregivers = User.query.filter_by(role='caregiver', is_active=True).limit(4).all()
    return render_template('public/about.html', cms_about=cms_about, caregivers=caregivers)

@public_bp.route('/services')
def services():
    category = request.args.get('category')
    search = request.args.get('search')
    query = Service.query.filter_by(is_active=True)
    if category and category != 'all':
        query = query.filter_by(category=category)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Service.name.ilike(s)) | (Service.description.ilike(s)))
    services_list = query.all()
    
    # Unique categories
    categories = sorted(list(set(s.category for s in Service.query.filter_by(is_active=True).all())))
    return render_template('public/services.html', services=services_list, categories=categories, selected_category=category, search=search)

@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        flash('Thank you for reaching out! Our elder care coordinators will get in touch with you promptly.', 'success')
        return redirect(url_for('public.contact'))
    cms_contact = Page.query.filter_by(slug='contact', status='published').first()
    return render_template('public/contact.html', cms_contact=cms_contact)

@public_bp.route('/pages/<slug>')
def cms_page(slug):
    page = Page.query.filter_by(slug=slug.lower().strip(), status='published').first_or_404()
    return render_template('public/page.html', page=page)
