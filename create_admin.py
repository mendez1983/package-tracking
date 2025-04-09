from flask import Flask
from models import db, User
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///package_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Primero, eliminar el usuario admin si existe
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        db.session.delete(existing_admin)
        db.session.commit()
    
    # Crear nuevo usuario admin con método de hash específico
    admin = User(
        username='admin',
        email='admin@packtrack.com',
        password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Usuario admin creado exitosamente")