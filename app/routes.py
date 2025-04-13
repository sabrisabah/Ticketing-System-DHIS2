from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import Ticket, db, User, Notification
from .forms import TicketForm, UpdateTicketForm, LoginForm, AdminProfileForm, RegistrationForm
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Message
from . import mail
import logging
from flask_login import login_user, logout_user, login_required, current_user

main = Blueprint('main', __name__)

# Add before_request handler to protect all routes by default
@main.before_request
def check_auth():
    # List of routes that don't require authentication
    public_routes = ['static', 'main.login', 'main.register', 'main.submit_ticket']
    
    # Check if the current route is public
    if request.endpoint and request.endpoint not in public_routes:
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login', next=request.url))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
UPLOAD_FOLDER = 'app/static/uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_ticket_notification(ticket):
    admin_emails = current_app.config['ADMIN_EMAILS']
    if not admin_emails:
        logging.error('No admin emails configured. Check ADMIN_EMAILS in .env file')
        raise ValueError('No admin emails configured')
    
    if not current_app.config['MAIL_USERNAME'] or not current_app.config['MAIL_PASSWORD']:
        logging.error('Email credentials not configured. Check MAIL_USERNAME and MAIL_PASSWORD in .env file')
        raise ValueError('Email credentials not configured')
    
    try:
        subject = f'New Ticket #{ticket.id}: {ticket.program_name}'
        body = f'''A new ticket has been submitted:

Ticket ID: #{ticket.id}
Program: {ticket.program_name}
Type: {ticket.error_type}
Submitted By: {ticket.name} ({ticket.email})
Status: {ticket.status}

Description:
{ticket.description}

View ticket: {request.host_url.rstrip("/")}{url_for('main.ticket_detail', id=ticket.id)}
'''
        
        msg = Message(
            subject=subject,
            recipients=admin_emails,
            body=body,
            sender=current_app.config['MAIL_USERNAME']
        )
        
        if ticket.attachment_path:
            attachment_path = os.path.join(UPLOAD_FOLDER, ticket.attachment_path)
            if os.path.exists(attachment_path):
                with current_app.open_resource(attachment_path) as fp:
                    msg.attach(
                        ticket.attachment_path,
                        'application/octet-stream',
                        fp.read()
                    )
        
        mail.send(msg)
        logging.info(f'Email notification sent successfully for ticket #{ticket.id}')
    except Exception as e:
        logging.error(f'Failed to send email notification for ticket #{ticket.id}: {str(e)}')
        raise

def create_notification(ticket, user, message):
    # Only create notifications for:
    # 1. Admins when a new ticket is created
    # 2. Users when their ticket is updated by an admin
    if (user.username == 'admin' and ticket.status == 'Open') or \
       (user.id == ticket.user_id and current_user.username == 'admin'):
        notification = Notification(
            user_id=user.id,
            ticket_id=ticket.id,
            message=message
        )
        db.session.add(notification)
        db.session.commit()

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html', form=form)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/submit', methods=['GET', 'POST'])
def submit_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=form.name.data,
            email=form.email.data,
            program_name=form.program_name.data,
            error_type=form.error_type.data,
            description=form.description.data
        )
        
        if form.attachment.data:
            file = form.attachment.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                ticket.attachment_path = filename

        db.session.add(ticket)
        db.session.commit()
        
        # Create notifications for admin users only
        admins = User.query.filter_by(username='admin').all()
        for admin in admins:
            create_notification(ticket, admin, f"New ticket submitted for {ticket.program_name}: {ticket.error_type}")
        
        try:
            send_ticket_notification(ticket)
            flash('Your ticket has been submitted successfully and administrators have been notified!', 'success')
        except ValueError as ve:
            flash(f'Your ticket has been submitted successfully, but email notification failed: {str(ve)}', 'warning')
        except Exception as e:
            logging.error(f'Error sending notification: {str(e)}')
            flash('Your ticket has been submitted successfully, but there was an error sending the notification.', 'warning')
        
        return redirect(url_for('main.view_tickets'))
    return render_template('submit.html', form=form)

@main.route('/tickets')
@login_required
def view_tickets():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Ticket.query

    # If not admin, only show user's own tickets
    if not current_user.username == 'admin':
        query = query.filter(Ticket.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if search:
        query = query.filter(
            db.or_(
                Ticket.program_name.ilike(f'%{search}%'),
                Ticket.description.ilike(f'%{search}%')
            )
        )
    
    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('tickets.html', tickets=tickets)

@main.route('/ticket/<int:id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Check if user has permission to view this ticket
    if not current_user.username == 'admin' and ticket.user_id != current_user.id:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('main.view_tickets'))
    
    form = UpdateTicketForm(obj=ticket)
    
    # Only allow POST requests from admin users
    if request.method == 'POST':
        if current_user.username != 'admin':
            flash('You do not have permission to modify tickets.', 'danger')
            return redirect(url_for('main.view_tickets'))
            
        if form.validate_on_submit():
            old_status = ticket.status
            ticket.status = form.status.data
            ticket.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Notify the ticket owner about the status change
            if ticket.user_id:
                create_notification(ticket, User.query.get(ticket.user_id), 
                                f"Your ticket status has been updated from {old_status} to {ticket.status}")
            
            flash('Ticket status has been updated!', 'success')
            return redirect(url_for('main.view_tickets'))
        
    return render_template('ticket_detail.html', ticket=ticket, form=form)

@main.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    form = AdminProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        
        if form.password.data:
            current_user.set_password(form.password.data)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.admin_profile'))
    
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.phone_number.data = current_user.phone_number
    
    return render_template('admin_profile.html', form=form)

@main.route('/inbox')
@login_required
def inbox():
    if current_user.username == 'admin':
        # Admin sees all notifications
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .all()
    else:
        # Regular users only see notifications for their own tickets
        notifications = Notification.query\
            .join(Ticket, Notification.ticket_id == Ticket.id)\
            .filter(
                db.and_(
                    Notification.user_id == current_user.id,
                    Ticket.user_id == current_user.id
                )
            )\
            .order_by(Notification.created_at.desc())\
            .all()
    return render_template('inbox.html', notifications=notifications)

@main.route('/notification/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        flash('Notification marked as read.', 'success')
    return redirect(url_for('main.inbox'))