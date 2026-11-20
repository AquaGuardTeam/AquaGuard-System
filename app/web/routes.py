from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, Device, SensorReading, FilterAssessment, Alert, ValveEvent, Filter
from datetime import datetime, timedelta, timezone

_login_failures = {}

web = Blueprint('web', __name__)


@web.route('/')
@login_required
def dashboard():
    device = Device.query.first()
    reading = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()
    assessment = FilterAssessment.query.order_by(FilterAssessment.timestamp.desc()).first()
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    valve_event = ValveEvent.query.order_by(ValveEvent.requested_at.desc()).first()
    active_filter = Filter.query.filter_by(status='active').first()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    history = (SensorReading.query.filter(SensorReading.timestamp >= cutoff)
               .filter_by(validity_status='valid').order_by(SensorReading.timestamp.asc()).all())
    history_data = [{'timestamp': row.timestamp.isoformat(), 'tds_ppm': row.tds_ppm,
                     'turbidity_ntu': row.turbidity_ntu} for row in history]

    device_status = 'online'
    if not reading:
        device_status = 'offline'
    elif reading.timestamp.tzinfo is None:
        device_status = 'stale' if (datetime.now(timezone.utc).replace(tzinfo=None) - reading.timestamp).total_seconds() > 300 else 'online'
    elif (datetime.now(timezone.utc) - reading.timestamp).total_seconds() > 300:
        device_status = 'stale'

    test_data_enabled = False
    return render_template('dashboard.html', device=device, reading=reading,
                           assessment=assessment, alerts=alerts, history_data=history_data,
                           device_status=device_status, test_data_enabled=test_data_enabled,
                           valve_event=valve_event, active_filter=active_filter)


@web.route('/login', methods=['GET', 'POST'])
def login():
    if not User.query.first():
        flash('No account is provisioned. Contact the system super administrator.', 'danger')
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        now = datetime.utcnow()
        failures = _login_failures.get(username, [])
        failures = [attempt for attempt in failures if now - attempt < timedelta(minutes=10)]
        if len(failures) >= 5:
            flash('Too many sign-in attempts. Wait 10 minutes before trying again.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(request.form.get('password', '')):
            _login_failures.pop(username, None)
            login_user(user)
            return redirect(url_for('web.dashboard'))
        failures.append(now)
        _login_failures[username] = failures
        flash('Incorrect username or password.', 'danger')
    return render_template('login.html')


@web.route('/readings')
@login_required
def readings_page():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    readings = (SensorReading.query.filter(SensorReading.timestamp >= cutoff)
                .filter_by(validity_status='valid').order_by(SensorReading.timestamp.desc()).limit(200).all())
    device = Device.query.first()
    return render_template('readings.html', readings=readings, device=device)


@web.route('/alerts')
@login_required
def alerts_page():
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(100).all()
    return render_template('alerts.html', alerts=alerts)


@web.route('/kiosk')
def kiosk():
    session['kiosk'] = True
    device = Device.query.first()
    reading = SensorReading.query.filter_by(validity_status='valid').order_by(SensorReading.timestamp.desc()).first()
    assessment = FilterAssessment.query.order_by(FilterAssessment.timestamp.desc()).first()
    return render_template('kiosk.html', device=device, reading=reading, assessment=assessment)


@web.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not current_user.is_super_admin:
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        allowed_roles = ('admin', 'maintenance')

        if len(username) < 3:
            flash('Username must contain at least 3 characters.', 'danger')
        elif len(password) < 12:
            flash('Password must contain at least 12 characters.', 'danger')
        elif role not in allowed_roles:
            flash('Select a valid staff or user role.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('That username already exists.', 'danger')
        else:
            account = User(username=username, role=role)
            account.set_password(password)
            db.session.add(account)
            db.session.commit()
            flash(f'{username} was created with the {role} role.', 'success')

    users = User.query.order_by(User.created_at.asc()).all()
    return render_template('admin_users.html', users=users)


@web.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance_page():
    if not current_user.is_administrator:
        return redirect(url_for('web.dashboard'))
    from app.models import Filter, MaintenanceRecord

    if request.method == 'POST' and request.form.get('form_action') == 'register_filter':
        filter_type = request.form.get('filter_type', '').strip()
        installed_at = request.form.get('installed_at', '').strip()
        if not filter_type or not installed_at:
            flash('Enter the filter type and installation date.', 'danger')
        else:
            try:
                installed_date = datetime.fromisoformat(installed_at)
            except ValueError:
                flash('Enter a valid installation date.', 'danger')
            else:
                if installed_date.date() > datetime.now(timezone.utc).date():
                    flash('Installation date cannot be in the future.', 'danger')
                else:
                    active_filters = Filter.query.filter_by(device_id=Device.query.first().id, status='active').all()
                    for active in active_filters:
                        active.status = 'replaced'
                    db.session.add(Filter(device_id=Device.query.first().id,
                                          filter_type=filter_type,
                                          installed_at=installed_date,
                                          status='active'))
                    db.session.commit()
                    flash('Filter registration saved.', 'success')

    if request.method == 'POST' and request.form.get('form_action') != 'register_filter':
        action = request.form.get('action', '').strip()
        notes = request.form.get('notes', '').strip()
        filter_id = request.form.get('filter_id', type=int)
        event_date = request.form.get('event_date', '').strip()
        filter_row = db.session.get(Filter, filter_id) if filter_id else None
        if not action or not filter_row or not event_date:
            flash('Complete the filter, action, and date fields.', 'danger')
        else:
            try:
                parsed_date = datetime.fromisoformat(event_date)
            except ValueError:
                flash('Enter a valid service date.', 'danger')
            else:
                if parsed_date.date() > datetime.now(timezone.utc).date():
                    flash('Service date cannot be in the future.', 'danger')
                else:
                    record = MaintenanceRecord(filter_id=filter_row.id, event_date=parsed_date,
                                               action=action, notes=notes,
                                               recorded_by=current_user.id)
                    db.session.add(record)
                    if action.lower() in ('replaced', 'replacement'):
                        filter_row.replaced_at = parsed_date
                        filter_row.status = 'replaced'
                    db.session.commit()
                    flash('Maintenance record saved.', 'success')

    filters = Filter.query.all()
    records = MaintenanceRecord.query.order_by(MaintenanceRecord.event_date.desc()).all()
    return render_template('maintenance.html', filters=filters, records=records)


@web.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('web.login'))
