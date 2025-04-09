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