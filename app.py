# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps

# Importar bibliotecas adicionales para envío de correos
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importar modelos desde models
from models import db, Customer, Package, TrackingEvent, Notification, User, StatusEnum, PackageTypeEnum, NotificationMethodEnum
from sqlalchemy.exc import SQLAlchemyError

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///package_tracking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Inicializar la base de datos
db.init_app(app)
migrate = Migrate(app, db)

# Función para asegurar que el usuario esté autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Función para asegurar que el usuario sea administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('No tiene permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# Resto de las funciones de tu script original (send_email, etc.)
def send_email(to_email, subject, message):
    """
    Envía un correo electrónico usando SMTP
    """
    try:
        # Configura estas variables con tus credenciales de correo
        email_sender = "a.mendez@restoremastersllc.com"  # Cambia esto a tu dirección de correo real
        email_password = "lner mnyr kysw oupn"      # Cambia esto a tu contraseña real
        smtp_server = "smtp.gmail.com"        # Cambia esto según tu proveedor de correo
        smtp_port = 587                       # Cambia esto según tu proveedor de correo
        
        # Log detallado para depuración
        app.logger.info(f"Intentando enviar correo a {to_email}")
        app.logger.info(f"Asunto: {subject}")
        app.logger.info(f"Mensaje: {message[:100]}...")
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Añadir cuerpo del mensaje
        msg.attach(MIMEText(message, 'plain'))
        
        # Conectar y enviar
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)
        
        app.logger.info(f"Correo enviado correctamente a {to_email}")
        return True
    except Exception as e:
        app.logger.error(f"Error al enviar correo a {to_email}: {str(e)}")
        return True

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        
        flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Obtener conteo de paquetes por estado
    pending_count = Package.query.filter_by(status=StatusEnum.REGISTERED).count()
    processing_count = Package.query.filter_by(status=StatusEnum.PROCESSING).count()
    transit_count = Package.query.filter_by(status=StatusEnum.TRANSIT).count()
    customs_count = Package.query.filter_by(status=StatusEnum.CUSTOMS).count()
    delivery_count = Package.query.filter_by(status=StatusEnum.DELIVERY).count()
    delivered_count = Package.query.filter_by(status=StatusEnum.DELIVERED).count()
    
    # Obtener los últimos paquetes registrados
    recent_packages = Package.query.order_by(Package.registration_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           pending_count=pending_count,
                           processing_count=processing_count,
                           transit_count=transit_count,
                           customs_count=customs_count,
                           delivery_count=delivery_count,
                           delivered_count=delivered_count,
                           recent_packages=recent_packages)

@app.route('/admin/packages')
@admin_required
def admin_packages():
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    
    # Iniciar la consulta base
    query = Package.query
    
    # Aplicar filtro de búsqueda si se proporciona
    if search_query:
        query = query.filter(
            db.or_(
                Package.tracking_number.ilike(f'%{search_query}%'),
                Package.sender_name.ilike(f'%{search_query}%'),
                Package.recipient_name.ilike(f'%{search_query}%'),
                Package.sender_email.ilike(f'%{search_query}%'),
                Package.recipient_phone.ilike(f'%{search_query}%'),
                Package.sender_phone.ilike(f'%{search_query}%'),
                Package.destination_country_name.ilike(f'%{search_query}%')
            )
        )
    
    # Aplicar filtro de fecha si se proporciona
    if date_filter:
        try:
            # Convertir la fecha de string a datetime
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            # Filtrar paquetes por fecha de registro
            query = query.filter(db.func.date(Package.registration_date) == filter_date)
        except ValueError:
            # Manejar error de formato de fecha
            flash('Formato de fecha inválido', 'danger')
    
    # Aplicar filtro de estado si se proporciona
    if status_filter != 'all':
        # Convertir el string a la enumeración correspondiente
        status_enum = getattr(StatusEnum, status_filter.upper(), None)
        if status_enum:
            query = query.filter_by(status=status_enum)
    
    # Obtener resultados ordenados por fecha de registro (más recientes primero)
    packages = query.order_by(Package.registration_date.desc()).all()
    
    return render_template('admin/packages.html', 
                           packages=packages, 
                           StatusEnum=StatusEnum, 
                           search_query=search_query,
                           date_filter=date_filter)

@app.route('/register', methods=['GET', 'POST'])
def register_package():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            sender_name = request.form.get('sender_name')
            sender_email = request.form.get('sender_email')
            sender_phone = request.form.get('sender_phone')
            
            recipient_name = request.form.get('recipient_name')
            recipient_address = request.form.get('recipient_address')
            recipient_phone = request.form.get('recipient_phone')
            
            # Obtener la sucursal seleccionada
            branch = request.form.get('branch', 'irvin')  # Valor por defecto
            
            destination_country_code = request.form.get('destination_country')
            country_names = {
                'SLV': 'El Salvador',    
                'GTM': 'Guatemala',
                'USA': 'Estados Unidos',
                'MEX': 'México',
                'CAN': 'Canadá',
                'ESP': 'España',
                'COL': 'Colombia',
                'ARG': 'Argentina',
                'CHL': 'Chile',
                'PER': 'Perú',
                'BRA': 'Brasil',
                'OTH': 'Otro'
            }
            destination_country_name = country_names.get(destination_country_code, 'Desconocido')
            
            estimated_weight = float(request.form.get('estimated_weight'))
            
            # Convertir el tipo de paquete de string a enumeración
            package_type_str = request.form.get('package_type')
            
            # Mapear strings a valores de enumeración
            package_type_map = {
                'document': PackageTypeEnum.DOCUMENT,
                'box-small': PackageTypeEnum.BOX_SMALL,
                'box-medium': PackageTypeEnum.BOX_MEDIUM,
                'box-large': PackageTypeEnum.BOX_LARGE,
                'fragile': PackageTypeEnum.FRAGILE,
                'special': PackageTypeEnum.SPECIAL
            }
            
            if package_type_str in package_type_map:
                package_type = package_type_map[package_type_str]
            else:
                flash(f'Tipo de paquete no válido: {package_type_str}', 'danger')
                return redirect(url_for('register_package'))
            
            # Buscar o crear cliente
            customer = Customer.query.filter_by(email=sender_email).first()
            if not customer:
                customer = Customer(
                    name=sender_name,
                    email=sender_email,
                    phone=sender_phone
                )
                db.session.add(customer)
                db.session.flush()  # Para obtener el ID del cliente antes de usarlo
            
            # Calcular costo estimado
            estimated_cost = estimated_weight * 17.00
            
            # Crear paquete
            package = Package(
                customer_id=customer.id,
                sender_name=sender_name,
                sender_email=sender_email,
                sender_phone=sender_phone,
                recipient_name=recipient_name,
                recipient_address=recipient_address,
                recipient_phone=recipient_phone,
                destination_country_code=destination_country_code,
                destination_country_name=destination_country_name,
                estimated_weight=estimated_weight,
                estimated_cost=estimated_cost,
                package_type=package_type,
                branch=branch  # Añadir la sucursal
            )
            
            db.session.add(package)
            
            # Crear evento inicial
            event = TrackingEvent(
                package=package,
                location="Oficina Central",
                status=StatusEnum.REGISTERED,
                description="Paquete registrado"
            )
            db.session.add(event)
            
            db.session.commit()
            
            # Mostrar confirmación
            flash(f'Paquete registrado con éxito. Número de rastreo: {package.tracking_number}', 'success')
            return render_template('confirmation.html', package=package)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el paquete: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/track', methods=['GET', 'POST'])
def track_package():
    package = None
    events = None
    
    if request.method == 'POST' or request.args.get('tracking_number'):
        tracking_number = request.form.get('tracking_number') or request.args.get('tracking_number')
        
        if tracking_number:
            package = Package.query.filter_by(tracking_number=tracking_number).first()
            
            if package:
                events = TrackingEvent.query.filter_by(package_id=package.id).order_by(TrackingEvent.date.desc()).all()
            else:
                flash('Número de rastreo no encontrado. Por favor verifique e intente nuevamente.', 'warning')
    
    return render_template('track.html', package=package, events=events, StatusEnum=StatusEnum)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    # Obtener parámetros de filtro
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    branch = request.args.get('branch', 'all')  # Nuevo filtro por sucursal
    
    # Crear consulta base
    query = Package.query
    
    # Aplicar filtros si existen
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_date = start_date.replace(hour=0, minute=0, second=0)
            query = query.filter(Package.registration_date >= start_date)
        except ValueError:
            flash('Formato de fecha inicial inválido', 'danger')
            return redirect(url_for('admin_reports'))
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Package.registration_date <= end_date)
        except ValueError:
            flash('Formato de fecha final inválido', 'danger')
            return redirect(url_for('admin_reports'))
    
    # Aplicar filtro de sucursal si no es 'all'
    if branch != 'all':
        query = query.filter(Package.branch == branch)
    
    # Obtener paquetes ordenados por fecha
    try:
        all_packages = query.order_by(Package.registration_date.desc()).all()
        
        # Agrupar por fecha
        packages_by_date = {}
        total_revenue = 0
        
        for package in all_packages:
            date_str = package.registration_date.strftime('%Y-%m-%d')
            if date_str not in packages_by_date:
                packages_by_date[date_str] = {
                    'count': 0,
                    'revenue': 0,
                    'packages': []
                }
            
            # Usar el costo final si existe, de lo contrario usar el estimado
            package_cost = package.final_cost if package.final_cost else package.estimated_cost
            
            packages_by_date[date_str]['count'] += 1
            packages_by_date[date_str]['revenue'] += package_cost
            packages_by_date[date_str]['packages'].append(package)
            
            total_revenue += package_cost
        
        # Convertir a lista y ordenar por fecha (más reciente primero)
        report_data = []
        for date_str, data in packages_by_date.items():
            report_data.append({
                'date': date_str,
                'count': data['count'],
                'revenue': data['revenue'],
                'packages': data['packages']
            })
        
        report_data.sort(key=lambda x: x['date'], reverse=True)
        
        # Obtener estadísticas generales
        total_packages = len(all_packages)
        
        # Obtener lista de sucursales únicas para el filtro
        branches = db.session.query(Package.branch).distinct().all()
        branches = [b[0] for b in branches]
        
        # Formatear fechas para mostrar
        formatted_start_date = start_date.strftime('%d/%m/%Y') if start_date_str else ''
        formatted_end_date = end_date.strftime('%d/%m/%Y') if end_date_str else ''
        
        return render_template('admin/reports.html',
                             report_data=report_data,
                             total_packages=total_packages,
                             total_revenue=total_revenue,
                             start_date=formatted_start_date,
                             end_date=formatted_end_date,
                             branches=branches,
                             selected_branch=branch)
    
    except Exception as e:
        app.logger.error(f"Error generando reporte: {str(e)}")
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('admin_reports'))

@app.route('/admin/package/<tracking_number>', methods=['GET', 'POST'])
@admin_required
def admin_package_detail(tracking_number):
    package = Package.query.filter_by(tracking_number=tracking_number).first_or_404()
    events = TrackingEvent.query.filter_by(package_id=package.id).order_by(TrackingEvent.date.desc()).all()
    
    if request.method == 'POST':
        # Verificar si el paquete ya está entregado
        if package.status == StatusEnum.DELIVERED:
            flash('No se pueden realizar modificaciones en un paquete que ya ha sido entregado.', 'warning')
            return redirect(url_for('admin_package_detail', tracking_number=tracking_number))
            
        action = request.form.get('action')
        
        if action == 'update_status':
            try:
                # Actualizar peso real si se proporcionó
                if request.form.get('actual_weight'):
                    package.actual_weight = float(request.form.get('actual_weight'))
                    package.final_cost = package.calculate_final_cost()
                
                # Actualizar estado
                new_status_str = request.form.get('status')
                old_status = package.status.value  # Guardar estado anterior para comparación
                
                if new_status_str:
                    # Convertir el string a la enumeración correspondiente
                    new_status_enum = getattr(StatusEnum, new_status_str.upper(), None)
                    if new_status_enum and new_status_enum != package.status:
                        package.status = new_status_enum
                
                # Actualizar ubicación
                location = request.form.get('location')
                notes = request.form.get('notes')
                
                # Determinar descripción del evento según el estado
                status_descriptions = {
                    'processing': 'Paquete procesado',
                    'transit': 'En tránsito',
                    'customs': 'En proceso de aduana',
                    'delivery': 'En reparto',
                    'delivered': 'Entregado',
                    'returned': 'Devuelto',
                    'lost': 'Perdido'
                }
                description = status_descriptions.get(new_status_str, 'Estado actualizado')
                
                # Crear nuevo evento
                event = TrackingEvent(
                    package_id=package.id,
                    location=location,
                    status=new_status_enum,
                    description=description,
                    notes=notes,
                    created_by_id=session.get('user_id')
                )
                db.session.add(event)
                
                # Actualizar ubicación del paquete
                package.current_location = location
                
                # Si el paquete fue entregado, actualizar fecha de entrega y enviar notificación por correo
                if new_status_str == 'delivered' and old_status != 'delivered':
                    package.delivery_date = datetime.utcnow()
                    
                    # Enviar notificación por correo electrónico
                    email_message = f"""Estimado {package.sender_name},

Nos complace informarle que su paquete con número de rastreo {package.tracking_number} ha sido entregado el {package.delivery_date.strftime('%d/%m/%Y')} en {package.current_location}.

Gracias por confiar en PackTrack para sus envíos internacionales.

Atentamente,
El equipo de PackTrack"""

                    # Enviar correo
                    email_sent = send_email(package.sender_email, 
                                          "PackTrack - Notificación de Entrega", 
                                          email_message)
                    
                    # Registrar notificación en la base de datos
                    if email_sent:
                        email_notification = Notification(
                            package_id=package.id,
                            method=NotificationMethodEnum.EMAIL,
                            recipient=package.sender_email,
                            message=email_message
                        )
                        db.session.add(email_notification)
                    
                    # Marcar el paquete como notificado
                    package.notification_sent = True
                    
                    flash('Paquete actualizado y notificación de entrega enviada por correo electrónico', 'success')
                else:
                    flash('Paquete actualizado exitosamente', 'success')
                
                db.session.commit()
                
                return redirect(url_for('admin_package_detail', tracking_number=tracking_number))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar el paquete: {str(e)}', 'danger')
                
            return redirect(url_for('admin_package_detail', tracking_number=tracking_number))
    
    return render_template('admin/package_detail.html', package=package, events=events, StatusEnum=StatusEnum)

@app.route('/admin/notify/<tracking_number>', methods=['GET', 'POST'])
@admin_required
def admin_notify_delivery(tracking_number):
    package = Package.query.filter_by(tracking_number=tracking_number).first_or_404()
    
    if request.method == 'POST':
        method_str = request.form.get('method')
        message = request.form.get('message')
        
        try:
            # Convertir el string de método a la enumeración
            method_map = {
                'email': NotificationMethodEnum.EMAIL,
                'call': NotificationMethodEnum.CALL
            }
            
            if method_str not in method_map:
                flash(f'Método de notificación no válido: {method_str}', 'danger')
                return redirect(url_for('admin_notify_delivery', tracking_number=tracking_number))
                
            method = method_map[method_str]
            
            # Enviar notificación según el método seleccionado
            recipient = package.sender_email
            if method_str == 'email':
                send_email(recipient, "PackTrack - Notificación de Entrega", message)
            
            # Registrar notificación en la base de datos
            notification = Notification(
                package_id=package.id,
                method=method,
                recipient=recipient,
                message=message
            )
            db.session.add(notification)
            
            # Marcar el paquete como notificado
            package.notification_sent = True
            
            db.session.commit()
            
            flash('Notificación enviada exitosamente', 'success')
            return redirect(url_for('admin_package_detail', tracking_number=tracking_number))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al enviar la notificación: {str(e)}', 'danger')
    
    return render_template('admin/notify.html', package=package)

@app.route('/ticket/<tracking_number>')
@admin_required
def print_ticket(tracking_number):
    package = Package.query.filter_by(tracking_number=tracking_number).first_or_404()
    return render_template('ticket.html', package=package, now=datetime.utcnow())

@app.route('/label/<tracking_number>')
def print_label(tracking_number):
    package = Package.query.filter_by(tracking_number=tracking_number).first_or_404()
    return render_template('label.html', package=package, now=datetime.utcnow())

@app.route('/offline')
def offline():
    return render_template('offline.html')

# Incluir todas las rutas de registro de paquetes, notificaciones, etc. de tu script original

# Resto de las rutas de tu aplicación...

# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)