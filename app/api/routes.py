from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, current_app, session
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Device, SensorReading, Filter, MaintenanceRecord, FilterAssessment, Alert, ValveEvent, DispensingEvent
from app.domain.condition_classifier import ConditionClassifier

api = Blueprint('api', __name__)

from app import csrf


def authenticated_device():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    from werkzeug.security import check_password_hash
    for device in Device.query.all():
        if check_password_hash(device.api_token_hash, token):
            return device
    return None


from app import csrf


@csrf.exempt
@api.post('/readings')
def post_reading():
    device = authenticated_device()
    if not device:
        return jsonify(error='Invalid device credentials'), 401

    payload = request.get_json(silent=True) or {}
    required = ('timestamp', 'ph', 'tds_ppm', 'turbidity_ntu')
    if any(key not in payload for key in required):
        return jsonify(error='Missing required reading fields'), 400

    try:
        ph = float(payload['ph'])
        tds = float(payload['tds_ppm'])
        turbidity = float(payload['turbidity_ntu'])
        timestamp = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return jsonify(error='Invalid reading values'), 400

    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    stale_seconds = abs((now - timestamp).total_seconds())
    valid = (0 <= ph <= 14 and 0 <= tds <= 1000 and 0 <= turbidity <= 100
             and stale_seconds <= 300)

    reading = SensorReading(device_id=device.id, timestamp=timestamp, ph=ph,
                            tds_ppm=tds, turbidity_ntu=turbidity,
                            validity_status='valid' if valid else 'invalid')
    db.session.add(reading)
    db.session.flush()

    if not valid:
        db.session.add(Alert(device_id=device.id, reading_id=reading.id,
                             alert_type='invalid_reading', severity='warning',
                             message='Invalid or stale reading excluded from condition analysis.'))
        db.session.commit()
        return jsonify(error='Reading is invalid or stale and was excluded', id=reading.id), 422

    recent = SensorReading.query.filter_by(device_id=device.id, validity_status='valid').order_by(SensorReading.timestamp.desc()).limit(5).all()
    tds_values = [item.tds_ppm for item in reversed(recent)]
    turbidity_values = [item.turbidity_ntu for item in reversed(recent)]
    assessment = ConditionClassifier().classify(tds_values, turbidity_values)

    active_filter = Filter.query.filter_by(device_id=device.id, status='active').first()
    if active_filter:
        db.session.add(FilterAssessment(filter_id=active_filter.id, condition=assessment.condition.value,
                                        trend_summary=assessment.trend_summary,
                                        rule_version=assessment.rule_version))

    if assessment.condition.value == 'Critical':
        db.session.add(Alert(device_id=device.id, reading_id=reading.id, alert_type='critical_condition',
                             severity='critical', message='Critical TDS/turbidity trend. Flow shut-off is required.'))
        db.session.add(ValveEvent(device_id=device.id, command='close',
                                  reported_state='command_issued', feedback_available=False))

    db.session.commit()
    return jsonify(id=reading.id, condition=assessment.condition.value,
                   trend_summary=assessment.trend_summary), 201


@api.get('/kiosk/status')
def kiosk_status():
    reading = SensorReading.query.filter_by(validity_status='valid').order_by(SensorReading.timestamp.desc()).first()
    assessment = FilterAssessment.query.order_by(FilterAssessment.timestamp.desc()).first()
    response = {
        'condition': assessment.condition if assessment else 'Unknown',
        'timestamp': reading.timestamp.isoformat() if reading else None,
        'ph': reading.ph if reading else None,
        'tds_ppm': reading.tds_ppm if reading else None,
        'turbidity_ntu': reading.turbidity_ntu if reading else None,
        'dispensing_modes': ['cold', 'room_temperature'],
        'potability_notice': 'Post-filtration monitoring indicators.'
    }
    return jsonify(response)


@csrf.exempt
@api.post('/control/dispensing')
def dispensing_control():
    if not session.get('kiosk'):
        return jsonify(error='Dispensing is available only from the kiosk'), 403

    payload = request.get_json(silent=True) or {}
    mode = payload.get('mode')
    if mode not in ('cold', 'room_temperature'):
        return jsonify(error='Mode must be cold or room_temperature'), 400

    device = Device.query.first()
    assessment = FilterAssessment.query.order_by(FilterAssessment.timestamp.desc()).first()
    if assessment and assessment.condition == 'Critical':
        event = DispensingEvent(device_id=device.id, mode=mode,
                                reported_state='blocked_critical_condition', feedback_available=False)
        db.session.add(event)
        db.session.commit()
        return jsonify(id=event.id, accepted=False,
                       reported_state='blocked_critical_condition'), 409

    event = DispensingEvent(device_id=device.id, mode=mode,
                            reported_state='command_issued', feedback_available=False)
    db.session.add(event)
    db.session.commit()
    return jsonify(id=event.id, mode=mode, accepted=True,
                   reported_state='command_issued', feedback_available=False), 201


@csrf.exempt
@api.post('/control/dispensing/stop')
def stop_dispensing():
    if not session.get('kiosk'):
        return jsonify(error='Stop control is available only from the kiosk'), 403
    device = Device.query.first()
    event = DispensingEvent(device_id=device.id, mode='stop',
                            reported_state='stopped', feedback_available=False)
    db.session.add(event)
    db.session.commit()
    return jsonify(id=event.id, accepted=True, reported_state='stopped'), 200


@api.get('/control/dispensing/latest')
def latest_dispensing_control():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    expected = current_app.config.get('DEVICE_API_TOKEN')
    if not expected or token != expected:
        return jsonify(error='Invalid device credentials'), 401
    event = DispensingEvent.query.order_by(DispensingEvent.requested_at.desc()).first()
    if not event:
        return jsonify(mode=None, command='none')
    command = 'stop' if event.mode == 'stop' else 'dispense'
    return jsonify(id=event.id, mode=event.mode, command=command,
                   reported_state=event.reported_state,
                   requested_at=event.requested_at.isoformat())


@api.get('/readings/latest')
@login_required
def latest_reading():
    device_id = request.args.get('device_id', type=int)
    query = SensorReading.query.filter_by(validity_status='valid')
    if device_id:
        query = query.filter_by(device_id=device_id)
    reading = query.order_by(SensorReading.timestamp.desc()).first()
    if not reading:
        return jsonify(error='No valid readings found'), 404
    return jsonify(id=reading.id, device_id=reading.device_id, timestamp=reading.timestamp.isoformat(),
                   ph=reading.ph, tds_ppm=reading.tds_ppm, turbidity_ntu=reading.turbidity_ntu)


@api.get('/readings/history')
@login_required
def reading_history():
    device_id = request.args.get('device_id', type=int)
    hours = request.args.get('hours', 24, type=int)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = SensorReading.query.filter(SensorReading.timestamp >= cutoff)
    if device_id:
        query = query.filter_by(device_id=device_id)
    readings = query.order_by(SensorReading.timestamp.asc()).limit(500).all()
    return jsonify([{'timestamp': item.timestamp.isoformat(), 'ph': item.ph,
                     'tds_ppm': item.tds_ppm, 'turbidity_ntu': item.turbidity_ntu}
                    for item in readings])


@api.get('/devices')
@login_required
def devices():
    return jsonify([{'id': d.id, 'name': d.name, 'location': d.location, 'status': d.status} for d in Device.query.all()])


@api.get('/assessments/latest')
@login_required
def latest_assessment():
    assessment = FilterAssessment.query.order_by(FilterAssessment.timestamp.desc()).first()
    if not assessment:
        return jsonify(        condition='Unknown', trend_summary='No valid assessment data', rule_version='AG-RULE-1.0')
    return jsonify(condition=assessment.condition, trend_summary=assessment.trend_summary,
                   rule_version=assessment.rule_version)


@api.get('/alerts')
@login_required
def alerts():
    rows = Alert.query.order_by(Alert.created_at.desc()).limit(50).all()
    return jsonify([{'id': r.id, 'severity': r.severity, 'message': r.message,
                     'created_at': r.created_at.isoformat(), 'status': r.status} for r in rows])


@api.route('/filters', methods=['GET', 'POST'])
@login_required
def filters():
    if request.method == 'GET':
        rows = Filter.query.all()
        return jsonify([{'id': r.id, 'filter_type': r.filter_type, 'installed_at': r.installed_at.isoformat(),
                         'status': r.status} for r in rows])
    if not current_user.is_administrator:
        return jsonify(error='Administrator role required'), 403
    payload = request.get_json(silent=True) or {}
    try:
        row = Filter(device_id=int(payload['device_id']), filter_type=payload['filter_type'],
                     installed_at=datetime.fromisoformat(payload['installed_at'].replace('Z', '+00:00')))
    except (KeyError, TypeError, ValueError):
        return jsonify(error='Invalid filter fields'), 400
    db.session.add(row)
    db.session.commit()
    return jsonify(id=row.id), 201


@api.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance():
    if request.method == 'GET':
        rows = MaintenanceRecord.query.order_by(MaintenanceRecord.event_date.desc()).all()
        return jsonify([{'id': r.id, 'filter_id': r.filter_id, 'event_date': r.event_date.isoformat(),
                         'action': r.action, 'notes': r.notes} for r in rows])
    if not current_user.is_administrator:
        return jsonify(error='Administrator role required'), 403
    payload = request.get_json(silent=True) or {}
    try:
        row = MaintenanceRecord(filter_id=int(payload['filter_id']), event_date=datetime.fromisoformat(payload['event_date'].replace('Z', '+00:00')),
                                action=payload['action'], notes=payload.get('notes', ''), recorded_by=current_user.id)
    except (KeyError, TypeError, ValueError):
        return jsonify(error='Invalid maintenance fields'), 400
    db.session.add(row)
    db.session.commit()
    return jsonify(id=row.id), 201


@api.post('/control/valve')
@login_required
def valve_control():
    if current_user.role not in ('super_admin', 'admin'):
        return jsonify(error='Administrator role required'), 403
    payload = request.get_json(silent=True) or {}
    command = payload.get('command')
    if command not in ('open', 'close'):
        return jsonify(error='Command must be open or close'), 400
    device_id = int(payload.get('device_id', 0))
    if not Device.query.get(device_id):
        return jsonify(error='Unknown device'), 404
    event = ValveEvent(device_id=device_id, user_id=current_user.id, command=command,
                       reported_state='command_issued', feedback_available=False)
    db.session.add(event)
    db.session.commit()
    return jsonify(id=event.id, reported_state='command_issued', feedback_available=False)


@api.get('/control/status')
def valve_status():
    event = ValveEvent.query.order_by(ValveEvent.requested_at.desc()).first()
    if not event:
        return jsonify(reported_state='unknown', feedback_available=False)
    return jsonify(reported_state=event.reported_state, feedback_available=event.feedback_available,
                   command=event.command, requested_at=event.requested_at.isoformat())
