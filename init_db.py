import os
import sys
from app import create_app
from app.extensions import db
from seed import seed_database

def init():
    print("Initializing Elden Care database...")
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    with app.app_context():
        db.create_all()
        print("Database schema verified/created successfully.")
        seed_database()

if __name__ == '__main__':
    init()
