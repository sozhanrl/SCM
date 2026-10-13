from datetime import datetime, timezone
from app.extensions import db

class Page(db.Model):
    __tablename__ = 'pages'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    meta_description = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='published', index=True) # 'published', 'draft'
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    author = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'meta_description': self.meta_description,
            'status': self.status,
            'created_by': self.created_by,
            'author_name': self.author.full_name if self.author else 'System',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Page {self.slug} ({self.status})>"


class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def get_url(self) -> str:
        return f"/uploads/media/{self.filename}"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_formatted': f"{self.file_size / 1024:.1f} KB" if self.file_size < 1048576 else f"{self.file_size / 1048576:.2f} MB",
            'mime_type': self.mime_type,
            'caption': self.caption,
            'url': self.get_url(),
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.full_name if self.uploader else 'System',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Media {self.filename}>"
