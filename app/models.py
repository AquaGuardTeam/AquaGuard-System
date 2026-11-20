from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import login_manager
from app.extensions import db


class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    api_token_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='online')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ph = db.Column(db.Float)
    tds_ppm = db.Column(db.Float)
    turbidity_ntu = db.Column(db.Float)
    validity_status = db.Column(db.String(20), nullable=False, default='valid')


class Filter(db.Model):
    __tablename__ = 'filters'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    filter_type = db.Column(db.String(120), nullable=False)
    installed_at = db.Column(db.DateTime, nullable=False)
    replaced_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default='active')


class MaintenanceRecord(db.Model):
    __tablename__ = 'maintenance_records'
    id = db.Column(db.Integer, primary_key=True)
    filter_id = db.Column(db.Integer, db.ForeignKey('filters.id'), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    action = db.Column(db.String(80), nullable=False)
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class FilterAssessment(db.Model):
    __tablename__ = 'filter_assessments'
    id = db.Column(db.Integer, primary_key=True)
    filter_id = db.Column(db.Integer, db.ForeignKey('filters.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    condition = db.Column(db.String(20), nullable=False)
    trend_summary = db.Column(db.String(255), nullable=False)
    rule_version = db.Column(db.String(30), nullable=False)


class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    reading_id = db.Column(db.Integer, db.ForeignKey('sensor_readings.id'), nullable=True)
    alert_type = db.Column(db.String(60), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False, default='open')


class ValveEvent(db.Model):
    __tablename__ = 'valve_events'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    command = db.Column(db.String(40), nullable=False)
    requested_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    reported_state = db.Column(db.String(40), nullable=False)
    feedback_available = db.Column(db.Boolean, nullable=False, default=False)


class DispensingEvent(db.Model):
    __tablename__ = 'dispensing_events'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    mode = db.Column(db.String(20), nullable=False)
    requested_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    reported_state = db.Column(db.String(40), nullable=False, default='requested')
    feedback_available = db.Column(db.Boolean, nullable=False, default=False)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='viewer')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_administrator(self):
        return self.role in ('super_admin', 'admin', 'maintenance')

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
