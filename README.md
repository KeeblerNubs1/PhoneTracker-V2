# NEMIS Guardian

A consent-based mobile device security and asset-tracking platform.

## Features
- Explicit device enrollment with per-device token
- Android foreground location reporting
- Python/Tkinter desktop dashboard
- Device inventory and health status
- Location history
- Geofencing alerts
- Audit logging
- HTTPS-ready FastAPI backend
- SQLite development database
- No hidden surveillance, credential theft, persistence, exploit payloads, or covert microphone/camera access

## Architecture

Android Agent -> HTTPS REST API -> SQLite/PostgreSQL
                              ^
                              |
                  Electron / Tkinter Dashboard

## Run the server

```bash
cd server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Open API docs at `http://127.0.0.1:8000/docs`.

## Run with Docker

Build and start the API with Docker Compose:

```bash
docker compose up --build -d
```

The API is available at `http://127.0.0.1:8000`, and the SQLite database is
stored in the named `nemis_guardian_data` volume so it persists across
container recreation. Stop the service with `docker compose down` (add
`--volumes` to remove the stored development data).

To build the API image directly from the repository root instead:

```bash
docker build -t nemis-guardian-api .
docker run --rm -p 8000:8000 -v nemis_guardian_data:/data nemis-guardian-api
```

## Run the desktop dashboard

```bash
cd desktop
pip install -r requirements.txt
python nemis_guardian.py
```

## Run the Electron desktop console

The Electron console provides forms for enrolling devices and recording
consented location and cell-tower observations, as well as an inventory view. It connects to the
local API at `http://127.0.0.1:8000` by default; the API address can be changed
in the application when needed.

```bash
cd desktop/electron
npm install
npm start
```

Cell-tower observations are sent by an explicitly enrolled device using its
token. The API records its MCC, MNC, area/cell identifiers, signal, and optional
coordinates; it does not directly connect to mobile carrier infrastructure or
locate devices that have not enrolled and reported their data.

## Android

The Android project is intentionally designed around visible, user-consented foreground location access. Configure the API URL and enrollment token in the app before use.

## Security

For production:
- Put the API behind TLS.
- Replace SQLite with PostgreSQL.
- Store device tokens as hashes.
- Add OAuth/OIDC + MFA for administrators.
- Use short-lived enrollment credentials.
- Encrypt sensitive records at rest.
- Rotate credentials.
- Keep immutable audit logs.
- Obtain consent and comply with applicable privacy/device-management laws.
