# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import enum

db = SQLAlchemy()

class StatusEnum(enum.Enum):
    REGISTERED = "registered"
    PROCESSING = "processing"
    TRANSIT = "transit"
    CUSTOMS = "customs"
    DELIVERY = "delivery"
    DELIVERED = "delivered"
    RETURNED = "returned"
    LOST = "lost"

class PackageTypeEnum(enum.Enum):
    DOCUMENT = "document"
    BOX_SMALL = "box-small"
    BOX_MEDIUM = "box-medium"
    BOX_LARGE = "box-large"
    FRAGILE = "fragile"
    SPECIAL = "special"

class NotificationMethodEnum(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    CALL = "call"

def generate_tracking_number():
    """Generate a unique tracking number with PKT prefix"""
    return f"PKT{uuid.uuid4().hex[:9].upper()}"

# Modelo para clientes
class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    packages = db.relationship('Package', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

# Modelo para paquetes
class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False, default=generate_tracking_number)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    branch = db.Column(db.String(50), nullable=False, default='irvin')
    # Información del remitente
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(100), nullable=False)
    sender_phone = db.Column(db.String(20), nullable=False)
    
    # Información del destinatario
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_address = db.Column(db.Text, nullable=False)
    recipient_phone = db.Column(db.String(20), nullable=False)
    destination_country_code = db.Column(db.String(3), nullable=False)
    destination_country_name = db.Column(db.String(50), nullable=False)
    
    # Información de peso y costo
    estimated_weight = db.Column(db.Float, nullable=False)
    actual_weight = db.Column(db.Float)
    estimated_cost = db.Column(db.Float, nullable=False)
    final_cost = db.Column(db.Float)
    
    # Información de tipo y estado
    package_type = db.Column(db.Enum(PackageTypeEnum), nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.REGISTERED, nullable=False)
    
    # Información de fechas
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delivery_date = db.Column(db.DateTime)
    
    # Ubicación actual
    current_location = db.Column(db.String(100), default="Oficina Central")
    
    # Notificaciones
    notification_sent = db.Column(db.Boolean, default=False)
    
    # Relaciones
    events = db.relationship('TrackingEvent', backref='package', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Package {self.tracking_number}>'
    
    def calculate_estimated_cost(self):
        """Calcula el costo estimado basado en el peso estimado"""
        COST_PER_POUND = 17.00
        return round(self.estimated_weight * COST_PER_POUND, 2)
    
    def calculate_final_cost(self):
        """Calcula el costo final basado en el peso real"""
        if not self.actual_weight:
            return None
        COST_PER_POUND = 17.00
        return round(self.actual_weight * COST_PER_POUND, 2)
    
    def add_event(self, location, description, notes=None, user_id=None):
        """Añade un nuevo evento de rastreo al paquete"""
        event = TrackingEvent(
            package_id=self.id,
            location=location,
            status=self.status,
            description=description,
            notes=notes,
            created_by_id=user_id
        )
        db.session.add(event)
        
        # Actualizar la ubicación actual del paquete
        self.current_location = location
        
        # Si el estado es 'entregado', actualizar la fecha de entrega
        if self.status == StatusEnum.DELIVERED and not self.delivery_date:
            self.delivery_date = datetime.utcnow()
            
        return event

# Modelo para eventos de rastreo
class TrackingEvent(db.Model):
    __tablename__ = 'tracking_events'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', backref='events')
    
    def __repr__(self):
        return f'<TrackingEvent {self.id}>'

# Modelo para notificaciones
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)
    package = db.relationship('Package', backref='notifications')
    method = db.Column(db.Enum(NotificationMethodEnum), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)  # email o número de teléfono
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Notification {self.id}>'

# Modelo para usuarios del sistema
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'