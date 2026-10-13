import os
from app import create_app
from app.extensions import db

app = create_app(os.getenv('FLASK_ENV', 'development'))

with app.app_context():
    # Automatically ensure tables exist
    db.create_all()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
