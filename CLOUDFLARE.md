# AquaGuard Cloudflare Deployment

## Required architecture

- ESP32 -> HTTPS REST API
- Flask + MySQL -> Cloudflare Tunnel origin
- `/kiosk` -> Cloudflare hostname limited to fountain touchscreen
- `/login`, `/`, `/maintenance`, `/admin/users` -> Cloudflare Access
- No direct public access to the Flask origin

## Flask deployment

Use a Linux host or Raspberry Pi, MySQL, a production WSGI server, and HTTPS. Bind Gunicorn to `127.0.0.1:5000` only.

```text
SECRET_KEY=<random 32+ bytes>
DEVICE_API_TOKEN=<unique ESP32 token>
KIOSK_API_TOKEN=<reserved kiosk secret>
SUPER_ADMIN_USERNAME=<provisioned>
SUPER_ADMIN_PASSWORD=<strong unique password>
SESSION_COOKIE_SECURE=true
DATABASE_URL=mysql+pymysql://aquaguard:<password>@127.0.0.1/aquaguard
```

Do not expose port 5000 through a router or firewall.

## Cloudflare Tunnel

Create a Tunnel and public hostnames:

- `aquaguard.example.edu/kiosk` -> `http://127.0.0.1:5000/kiosk`
- `admin.aquaguard.example.edu` -> `http://127.0.0.1:5000`
- `api.aquaguard.example.edu` -> `http://127.0.0.1:5000`

Restrict the admin hostname and protected API routes with Cloudflare Access. The kiosk hostname should allow only the kiosk network/location and receive no administrative paths.

Create a route block that prevents `/admin/*`, `/maintenance`, `/login`, `/api/filters`, `/api/maintenance`, `/api/control/valve`, `/api/control/status`, and `/api/control/dispensing/latest` from being reached through the public kiosk hostname.

## ESP32

Use an HTTPS API URL and a CA certificate. The ESP32 submits `/api/readings` with its bearer token and polls `/api/control/dispensing/latest` with the device token. It must fail safely and close/stop flow on a Critical assessment, network loss, invalid readings, restart, or power-loss behavior established in the hardware test plan.

## Kiosk

The kiosk browser opens only:

`https://aquaguard.example.edu/kiosk`

It may read `/api/kiosk/status` and request Cold or Room Temperature through `/api/control/dispensing`. It must not display filter records, staff identities, valve commands, or account management.

## Documented scope

AquaGuard uses rule-based TDS/turbidity moving averages and rates of change. It does not use trained machine-learning prediction or provide exact remaining filter life. pH is monitored and displayed only.
