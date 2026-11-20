# AquaGuard

AquaGuard is an IoT-based post-filtration water-monitoring, dispensing, and filter-maintenance prototype for a campus fountain.

## Stack

- ESP32 firmware: C/C++ using Arduino framework
- Backend: Python Flask REST API
- Database: MySQL in production; SQLite for local development
- Dashboard: HTML5, CSS, JavaScript, Bootstrap
- Icons: Font Awesome via Cloudflare CDN

## Start locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Provision the super administrator through the protected environment variables `SUPER_ADMIN_USERNAME` and `SUPER_ADMIN_PASSWORD` before first launch. There is no public registration page. the super administrator signs in to **Staff accounts** and creates administrator and maintenance accounts. Change temporary staff passwords after first sign-in.

The public kiosk is available at `http://127.0.0.1:5000/kiosk`. It shows only the latest status and selected indicators.

## Add accounts from the server terminal

Use the private terminal, never a public web registration page:

```powershell
python scripts/manage_users.py add --username test-admin --role admin
python scripts/manage_users.py add --username test-maintenance --role maintenance
python scripts/manage_users.py list
```

The command securely prompts for the temporary password and confirms it before saving a password hash. Roles:

- `super_admin`: user-account management and protected administration
- `admin`: protected operations and maintenance functions
- `maintenance`: filter and maintenance records

Students and faculty do not need login accounts. They use the local/public kiosk and dashboard view according to the document’s user roles.

The kiosk itself requires no account.

## Test

```powershell
pytest -q
```

The dashboard does not generate or seed sensor data. Unit tests use isolated data only. Real values appear only after the ESP32 submits authenticated readings.

## Deployment

Use HTTPS behind a production WSGI server and reverse proxy. Set `SECRET_KEY`, a unique `DEVICE_API_TOKEN`, `DATABASE_URL`, and `SESSION_COOKIE_SECURE=true`. Generate new credentials; never reuse local testing credentials. Use the MySQL schema and configure firewall rules so the ESP32 can reach only the API endpoint.

## Safety and scope

- pH, TDS, and turbidity are post-filtration indicators.
- pH is displayed but is not used by the current rule classifier.
- Cold and Room Temperature are the only dispensing modes.
- A Critical TDS/turbidity assessment takes priority and must close or stop water flow.
- Valve events distinguish issued commands, ESP32-reported states, and physical feedback.
- The solenoid valve requires a separate regulated 12 V supply through a compatible relay or driver. It must not be powered from an ESP32 GPIO.
- The exact cooling unit, touchscreen, pump, valve, and relay datasheets remain to be confirmed before fabrication.

## MySQL

Set `DATABASE_URL` in `.env`, for example:

```text
mysql+pymysql://aquaguard_user:password@localhost/aquaguard
```

The SQL reference schema is in `schema.sql`.
