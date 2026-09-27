from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import os
import sqlite3
import secrets

# Set NEMIS_DB_PATH when deploying so the SQLite database can live on a
# persistent volume rather than inside the application image.
DB = os.getenv("NEMIS_DB_PATH", "nemis_guardian.db")
app = FastAPI(title="NEMIS Guardian API", version="1.0.0")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        token TEXT NOT NULL,
        enrolled_at TEXT NOT NULL,
        last_seen TEXT,
        battery REAL,
        latitude REAL,
        longitude REAL,
        accuracy REAL
    );
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        accuracy REAL
    );
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        device_id TEXT,
        detail TEXT
    );
    CREATE TABLE IF NOT EXISTS cell_towers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        radio_type TEXT NOT NULL,
        mobile_country_code INTEGER NOT NULL,
        mobile_network_code INTEGER NOT NULL,
        area_code INTEGER NOT NULL,
        cell_id INTEGER NOT NULL,
        signal_dbm REAL,
        latitude REAL,
        longitude REAL,
        accuracy REAL
    );
    """)
    c.commit()
    c.close()

init()

class Enrollment(BaseModel):
    device_id: str = Field(min_length=3, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    platform: str = Field(default="android", max_length=32)

class LocationReport(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None = None
    battery: float | None = None
    timestamp: str | None = None

class CellTowerReport(BaseModel):
    """A tower observation reported by an enrolled, consenting device.

    The server records observations and does not communicate with carrier
    infrastructure or locate un-enrolled phones.
    """
    radio_type: str = Field(default="lte", min_length=1, max_length=32)
    mobile_country_code: int = Field(ge=0, le=999)
    mobile_network_code: int = Field(ge=0, le=999)
    area_code: int = Field(ge=0)
    cell_id: int = Field(ge=0)
    signal_dbm: float | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0)
    timestamp: str | None = None

def audit(action, device_id=None, detail=""):
    c = db()
    c.execute(
        "INSERT INTO audit(timestamp,action,device_id,detail) VALUES(?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), action, device_id, detail)
    )
    c.commit()
    c.close()

@app.get("/health")
def health():
    return {"status": "ok", "service": "NEMIS Guardian"}

@app.post("/devices/enroll")
def enroll(req: Enrollment):
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).isoformat()
    c = db()
    try:
        c.execute(
            "INSERT INTO devices(device_id,name,platform,token,enrolled_at) VALUES(?,?,?,?,?)",
            (req.device_id, req.name, req.platform, token, now)
        )
        c.commit()
    except sqlite3.IntegrityError:
        c.close()
        raise HTTPException(409, "Device already enrolled")
    c.close()
    audit("DEVICE_ENROLLED", req.device_id, req.platform)
    return {"device_id": req.device_id, "token": token}

def authenticate(device_id: str, token: str | None):
    c = db()
    row = c.execute("SELECT * FROM devices WHERE device_id=?", (device_id,)).fetchone()
    c.close()
    if not row or not token or not secrets.compare_digest(row["token"], token):
        raise HTTPException(401, "Invalid device credentials")
    return row

@app.post("/devices/{device_id}/location")
def report_location(device_id: str, report: LocationReport, x_device_token: str | None = Header(default=None)):
    authenticate(device_id, x_device_token)
    ts = report.timestamp or datetime.now(timezone.utc).isoformat()
    c = db()
    c.execute("""INSERT INTO locations(device_id,timestamp,latitude,longitude,accuracy)
                 VALUES(?,?,?,?,?)""",
              (device_id, ts, report.latitude, report.longitude, report.accuracy))
    c.execute("""UPDATE devices SET last_seen=?,battery=?,latitude=?,longitude=?,accuracy=?
                 WHERE device_id=?""",
              (ts, report.battery, report.latitude, report.longitude,
               report.accuracy, device_id))
    c.commit()
    c.close()
    audit("LOCATION_REPORT", device_id)
    return {"accepted": True, "timestamp": ts}

@app.post("/devices/{device_id}/cell-towers")
def report_cell_tower(device_id: str, report: CellTowerReport, x_device_token: str | None = Header(default=None)):
    authenticate(device_id, x_device_token)
    ts = report.timestamp or datetime.now(timezone.utc).isoformat()
    c = db()
    c.execute("""INSERT INTO cell_towers(
                    device_id,timestamp,radio_type,mobile_country_code,mobile_network_code,
                    area_code,cell_id,signal_dbm,latitude,longitude,accuracy)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
              (device_id, ts, report.radio_type, report.mobile_country_code,
               report.mobile_network_code, report.area_code, report.cell_id,
               report.signal_dbm, report.latitude, report.longitude, report.accuracy))
    c.commit()
    c.close()
    audit("CELL_TOWER_REPORT", device_id, f"{report.radio_type}:{report.cell_id}")
    return {"accepted": True, "timestamp": ts}

@app.get("/devices")
def devices():
    c = db()
    rows = [dict(r) for r in c.execute(
        "SELECT id,device_id,name,platform,enrolled_at,last_seen,battery,latitude,longitude,accuracy FROM devices"
    ).fetchall()]
    c.close()
    return rows

@app.get("/devices/{device_id}/locations")
def locations(device_id: str, limit: int = 100):
    c = db()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM locations WHERE device_id=? ORDER BY timestamp DESC LIMIT ?",
        (device_id, min(max(limit, 1), 1000))
    ).fetchall()]
    c.close()
    return rows

@app.get("/devices/{device_id}/cell-towers")
def cell_towers(device_id: str, limit: int = 100):
    c = db()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM cell_towers WHERE device_id=? ORDER BY timestamp DESC LIMIT ?",
        (device_id, min(max(limit, 1), 1000))
    ).fetchall()]
    c.close()
    return rows

@app.get("/audit")
def audit_log(limit: int = 200):
    c = db()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM audit ORDER BY timestamp DESC LIMIT ?", (min(max(limit,1),1000),)
    ).fetchall()]
    c.close()
    return rows
