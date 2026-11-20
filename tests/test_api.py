import re

from app import create_app


def test_kiosk_status_is_read_only_and_limited():
    app = create_app()
    client = app.test_client()
    response = client.get('/api/kiosk/status')
    assert response.status_code == 200
    data = response.get_json()
    assert set(data) == {'condition', 'timestamp', 'ph', 'tds_ppm', 'turbidity_ntu', 'dispensing_modes', 'potability_notice'}


def test_public_setup_page_does_not_exist():
    app = create_app()
    response = app.test_client().get('/setup')
    assert response.status_code == 404


def test_readings_and_alerts_routes_require_login():
    app = create_app()
    client = app.test_client()
    assert client.get('/readings').status_code == 302
    assert client.get('/alerts').status_code == 302


def test_kiosk_dispensing_and_stop_workflow():
    app = create_app()
    client = app.test_client()
    client.get('/kiosk')
    dispense = client.post('/api/control/dispensing', json={'mode': 'cold'})
    assert dispense.status_code == 201
    stop = client.post('/api/control/dispensing/stop')
    assert stop.status_code == 200


def test_kiosk_stop_endpoint_is_session_bound():
    app = create_app()
    client = app.test_client()
    response = client.post('/api/control/dispensing/stop')
    assert response.status_code == 403


def test_room_and_cold_modes_are_only_accepted_modes():
    app = create_app()
    client = app.test_client()
    client.get('/kiosk')

    cold = client.post('/api/control/dispensing', json={'mode': 'cold'})
    assert cold.status_code == 201

    invalid = client.post('/api/control/dispensing', json={'mode': 'hot'})
    assert invalid.status_code == 400
