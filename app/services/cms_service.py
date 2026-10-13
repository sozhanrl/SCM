import os
import re
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.models.cms import Page, Media
from app.services.activity_service import log_activity

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def get_page_by_slug(slug: str, published_only: bool = True) -> Page | None:
    query = Page.query.filter_by(slug=slug.lower().strip())
    if published_only:
        query = query.filter_by(status='published')
    return query.first()

def get_all_pages(search: str = None, status: str = None):
    query = Page.query
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Page.title.ilike(s)) | (Page.slug.ilike(s)) | (Page.content.ilike(s)))
    if status and status != 'all':
        query = query.filter_by(status=status)
    return query.order_by(Page.title).all()

def create_page(data: dict, author_id: int) -> tuple[Page | None, list[str]]:
    errors = []
    title = data.get('title', '').strip()
    slug = data.get('slug', '').strip() or slugify(title)
    content = data.get('content', '').strip()
    meta_description = data.get('meta_description', '').strip() or None
    status = data.get('status', 'published')

    if not title:
        errors.append("Page title is required.")
    if not slug:
        errors.append("Page slug is required.")
    if not content:
        errors.append("Page content is required.")

    if Page.query.filter_by(slug=slug).first():
        errors.append(f"A page with the slug '{slug}' already exists.")

    if errors:
        return None, errors

    try:
        page = Page(
            title=title,
            slug=slug,
            content=content,
            meta_description=meta_description,
            status=status,
            created_by=author_id
        )
        db.session.add(page)
        db.session.commit()
        log_activity('CMS_PAGE_CREATED', user_id=author_id, details=f"Created CMS page '{title}' (slug: {slug})")
        return page, []
    except Exception as e:
        db.session.rollback()
        return None, [f"Failed to create page: {str(e)}"]

def update_page(page_id: int, data: dict, author_id: int) -> tuple[Page | None, list[str]]:
    page = db.session.get(Page, page_id)
    if not page:
        return None, ["Page not found."]

    errors = []
    title = data.get('title', '').strip()
    slug = data.get('slug', '').strip() or slugify(title)
    content = data.get('content', '').strip()
    meta_description = data.get('meta_description', '').strip() or None
    status = data.get('status', 'published')

    if not title:
        errors.append("Page title is required.")
    if not slug:
        errors.append("Page slug is required.")
    if not content:
        errors.append("Page content is required.")

    existing_slug = Page.query.filter(Page.slug == slug, Page.id != page_id).first()
    if existing_slug:
        errors.append(f"Another page already uses slug '{slug}'.")

    if errors:
        return None, errors

    try:
        page.title = title
        page.slug = slug
        page.content = content
        page.meta_description = meta_description
        page.status = status
        db.session.commit()
        log_activity('CMS_PAGE_UPDATED', user_id=author_id, details=f"Updated CMS page '{title}' (slug: {slug})")
        return page, []
    except Exception as e:
        db.session.rollback()
        return None, [f"Failed to update page: {str(e)}"]

def delete_page(page_id: int, admin_id: int) -> tuple[bool, str]:
    page = db.session.get(Page, page_id)
    if not page:
        return False, "Page not found."

    # Protect essential core pages like home, about, services, contact
    if page.slug in ('home', 'about', 'services', 'contact'):
        return False, f"The '{page.slug}' page is a core system page and cannot be deleted. You can edit its content instead."

    try:
        title = page.title
        db.session.delete(page)
        db.session.commit()
        log_activity('CMS_PAGE_DELETED', user_id=admin_id, details=f"Deleted CMS page '{title}'")
        return True, f"Page '{title}' has been deleted."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to delete page: {str(e)}"

# Media Management
def get_all_media():
    return Media.query.order_by(Media.created_at.desc()).all()

def save_media(file_storage, uploader_id: int, caption: str = None) -> tuple[Media | None, str | None]:
    if not file_storage or file_storage.filename == '':
        return None, "No file selected."

    filename = secure_filename(file_storage.filename)
    if not filename:
        return None, "Invalid file name."

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    allowed_exts = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp', 'gif'})
    if ext not in allowed_exts:
        return None, f"File format '.{ext}' is not permitted. Allowed: {', '.join(allowed_exts)}"

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    if size > max_size:
        return None, f"File size exceeds maximum allowed size ({max_size // 1048576} MB)."

    unique_filename = f"media_{uuid.uuid4().hex[:10]}.{ext}"
    media_dir = current_app.config['MEDIA_UPLOAD_FOLDER']
    os.makedirs(media_dir, exist_ok=True)
    save_path = os.path.join(media_dir, unique_filename)

    mime_type = file_storage.content_type or 'application/octet-stream'

    try:
        file_storage.save(save_path)
        media = Media(
            filename=unique_filename,
            original_filename=filename,
            file_path=save_path,
            file_size=size,
            mime_type=mime_type,
            caption=caption.strip() if caption else filename,
            uploaded_by=uploader_id
        )
        db.session.add(media)
        db.session.commit()
        log_activity('MEDIA_UPLOADED', user_id=uploader_id, details=f"Uploaded media: {unique_filename} ({filename})")
        return media, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to save media: {str(e)}"

def delete_media(media_id: int, admin_id: int) -> tuple[bool, str]:
    media = db.session.get(Media, media_id)
    if not media:
        return False, "Media item not found."

    media_dir = current_app.config['MEDIA_UPLOAD_FOLDER']
    file_path = os.path.join(media_dir, media.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    try:
        db.session.delete(media)
        db.session.commit()
        log_activity('MEDIA_DELETED', user_id=admin_id, details=f"Deleted media ID {media_id} ({media.filename})")
        return True, "Media deleted successfully."
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to delete media record: {str(e)}"
