# init_db.py
from werkzeug.security import generate_password_hash
from flask import Flask
from models import db, User, Package, Customer, TrackingEvent, StatusEnum
from datetime import datetime, timedelta
import random

# Crear la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-development'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///package_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db.init_app(app)

# Función para crear datos de prueba
def create_sample_data():
    # Crear usuario administrador
    admin = User(
        username='admin',
        email='admin@packtrack.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    
    # Crear algunos clientes de ejemplo
    customers = [
        Customer(name='Juan Pérez', email='juan.perez@example.com', phone='555-123-4567'),
        Customer(name='María García', email='maria.garcia@example.com', phone='555-765-4321'),
        Customer(name='Roberto González', email='roberto.gonzalez@example.com', phone='555-987-6543'),
        Customer(name='Ana Rodríguez', email='ana.rodriguez@example.com', phone='555-321-7654')
    ]
    
    for customer in customers:
        db.session.add(customer)
    
    db.session.commit()  # Commit para obtener IDs de clientes
    
    # Países de destino disponibles
    countries = {
        'USA': 'Estados Unidos',
        'ESA': 'El Salvador',
        'CAN': 'Canadá',
        'ESP': 'España',
        'COL': 'Colombia',
        'ARG': 'Argentina',
        'CHL': 'Chile',
        'PER': 'Perú',
        'BRA': 'Brasil'
    }
    
    # Lista de posibles ubicaciones por estado
    locations = {
        'registered': ['Oficina Central'],
        'processing': ['Centro de Distribución', 'Almacén Principal', 'Oficina Central'],
        'transit': ['Aeropuerto Internacional', 'Puerto de Carga', 'En ruta a destino'],
        'customs': ['Aduana de Estados Unidos', 'Aduana de El Salvador', 'Aduana de España', 'Aduana de Colombia'],
        'delivery': ['Centro de Distribución Local', 'En ruta de entrega'],
        'delivered': ['Domicilio del destinatario']
    }
    
    # Crear paquetes de ejemplo
    for i in range(1, 21):  # Crear 20 paquetes
        # Seleccionar cliente aleatorio
        customer = random.choice(customers)
        
        # Seleccionar país aleatorio
        country_code = random.choice(list(countries.keys()))
        country_name = countries[country_code]
        
        # Crear peso estimado y real
        estimated_weight = round(random.uniform(0.5, 20.0), 1)
        actual_weight = round(estimated_weight * random.uniform(0.9, 1.1), 1)  # Variación aleatoria
        
        # Calcular costos
        estimated_cost = round(estimated_weight * 17.0, 2)
        final_cost = round(actual_weight * 17.0, 2)
        
        # Determinar estado según posición en la lista
        if i <= 5:
            status = StatusEnum.REGISTERED
            actual_weight = None
            final_cost = None
        elif i <= 8:
            status = StatusEnum.PROCESSING
        elif i <= 12:
            status = StatusEnum.TRANSIT
        elif i <= 15:
            status = StatusEnum.CUSTOMS
        elif i <= 17:
            status = StatusEnum.DELIVERY
        else:
            status = StatusEnum.DELIVERED
        
        # Calcular fechas
        days_ago = random.randint(1, 30)
        registration_date = datetime.now() - timedelta(days=days_ago)
        delivery_date = datetime.now() - timedelta(days=random.randint(0, 3)) if status == StatusEnum.DELIVERED else None
        
        # Crear paquete
        package = Package(
            tracking_number=f"PKT{str(i).zfill(9)}",
            customer_id=customer.id,
            sender_name=customer.name,
            sender_email=customer.email,
            sender_phone=customer.phone,
            recipient_name=f"Destinatario {i}",
            recipient_address=f"Calle Principal #{random.randint(100, 999)}, {country_name}",
            recipient_phone=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            destination_country_code=country_code,
            destination_country_name=country_name,
            estimated_weight=estimated_weight,
            actual_weight=actual_weight,
            estimated_cost=estimated_cost,
            final_cost=final_cost,
            package_type=random.choice(['document', 'box-small', 'box-medium', 'box-large', 'fragile', 'special']),
            status=status,
            registration_date=registration_date,
            delivery_date=delivery_date,
            current_location=random.choice(locations[status.value]),
            notification_sent=True if status == StatusEnum.DELIVERED and random.choice([True, False]) else False
        )
        
        db.session.add(package)
        db.session.flush()  # Para obtener el ID del paquete
        
        # Crear eventos de rastreo
        # Registrado (todos los paquetes lo tienen)
        event_registered = TrackingEvent(
            package_id=package.id,
            date=registration_date,
            location='Oficina Central',
            status=StatusEnum.REGISTERED,
            description='Paquete registrado'
        )
        db.session.add(event_registered)
        
        event_date = registration_date
        
        # Si ya está procesado o en un estado posterior
        if status.value != 'registered':
            event_date += timedelta(hours=random.randint(2, 24))
            event_processing = TrackingEvent(
                package_id=package.id,
                date=event_date,
                location=random.choice(locations['processing']),
                status=StatusEnum.PROCESSING,
                description='Paquete procesado',
                notes='Peso verificado' if actual_weight else None
            )
            db.session.add(event_processing)
        
        # Si está en tránsito o un estado posterior
        if status.value in ['transit', 'customs', 'delivery', 'delivered']:
            event_date += timedelta(hours=random.randint(6, 48))
            event_transit = TrackingEvent(
                package_id=package.id,
                date=event_date,
                location=random.choice(locations['transit']),
                status=StatusEnum.TRANSIT,
                description='En tránsito internacional'
            )
            db.session.add(event_transit)
        
        # Si está en aduanas o un estado posterior
        if status.value in ['customs', 'delivery', 'delivered']:
            event_date += timedelta(hours=random.randint(12, 72))
            event_customs = TrackingEvent(
                package_id=package.id,
                date=event_date,
                location=random.choice(locations['customs']),
                status=StatusEnum.CUSTOMS,
                description='En proceso de aduana'
            )
            db.session.add(event_customs)
        
        # Si está en reparto o ya fue entregado
        if status.value in ['delivery', 'delivered']:
            event_date += timedelta(hours=random.randint(4, 24))
            event_delivery = TrackingEvent(
                package_id=package.id,
                date=event_date,
                location=random.choice(locations['delivery']),
                status=StatusEnum.DELIVERY,
                description='En reparto'
            )
            db.session.add(event_delivery)
        
        # Si ya fue entregado
        if status.value == 'delivered':
            event_date += timedelta(hours=random.randint(1, 8))
            event_delivered = TrackingEvent(
                package_id=package.id,
                date=event_date,
                location=random.choice(locations['delivered']),
                status=StatusEnum.DELIVERED,
                description='Paquete entregado',
                notes='Firmado por el destinatario'
            )
            db.session.add(event_delivered)
    
    db.session.commit()
    
    print("Base de datos inicializada con datos de ejemplo.")


# Crear tablas y datos de ejemplo
def init_db():
    with app.app_context():
        db.create_all()
        print("Tablas creadas correctamente.")

if __name__ == "__main__":
    init_db()


# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///package_tracking.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Configuraciones adicionales para producción
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# Seleccionar configuración según el entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


# run.py (Script principal para ejecutar la aplicación)
import os
from app import app
from config import config

# Configurar la aplicación según el entorno
app_env = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[app_env])

# Función para crear contexto para comandos de Flask
@app.shell_context_processor
def make_shell_context():
    from models import db, Customer, Package, TrackingEvent, User, Notification
    return {
        'db': db,
        'Customer': Customer,
        'Package': Package,
        'TrackingEvent': TrackingEvent,
        'User': User,
        'Notification': Notification
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))