import json
import gzip
import hashlib
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA_FILE = Path("crime_backend_data.json")
REPORT_FILE = Path("hotspot_report.json")
STARTED_AT = datetime.now()

DEFAULT_DB = {
    "users": [], # Stores {id, name, email, password, token, role}
    "complaints": [],
    "cases": [],
    "watch": [],
    "feedback": [],
    "cyber": [],
    "cctv": [],
    "sos": [],  # Emergency SOS alerts
    "audit": [],
    "stations": [
        {"name": "Central Station", "officers_total": 12},
        {"name": "North Station", "officers_total": 10},
        {"name": "South Station", "officers_total": 8},
    ],
}


def load_db() -> dict:
    if not DATA_FILE.exists():
        return DEFAULT_DB.copy()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        for key, value in DEFAULT_DB.items():
            data.setdefault(key, value)
        return data
    except Exception:
        return DEFAULT_DB.copy()


def save_db(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_item(kind: str, payload: dict, limit: int) -> dict:
    db = load_db()
    item = dict(payload)
    item.setdefault("time", datetime.now().isoformat(timespec="seconds"))
    db[kind].insert(0, item)
    db[kind] = db[kind][:limit]
    save_db(db)
    return item


def parse_limit(value: str, default: int, max_value: int) -> int:
    try:
        return max(1, min(int(value), max_value))
    except (TypeError, ValueError):
        return default


def parse_offset(value: str, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_text(value: object) -> str:
    return str(value or "").strip().lower()


def filter_rows(kind: str, rows: list[dict], query: dict[str, list[str]]) -> list[dict]:
    status = normalize_text((query.get("status", [""])[0] or ""))
    district = normalize_text((query.get("district", [""])[0] or ""))
    actor = normalize_text((query.get("actor", [""])[0] or ""))
    text_q = normalize_text((query.get("q", [""])[0] or ""))
    since_dt = parse_iso_datetime((query.get("since", [""])[0] or ""))

    filtered = rows
    if status:
        filtered = [r for r in filtered if normalize_text(normalize_lifecycle(r.get("status"))) == status]
    elif query.get("exclude_solved", [""])[0].lower() in ["true", "1", "yes"]:
        filtered = [r for r in filtered if normalize_text(normalize_lifecycle(r.get("status"))) not in ["solved", "resolved", "closed"]]
    if district:
        filtered = [r for r in filtered if district in normalize_text(r.get("district"))]
    if actor:
        filtered = [r for r in filtered if actor in normalize_text(r.get("actor") or r.get("updated_by"))]
    if text_q:
        filtered = [
            r
            for r in filtered
            if text_q in normalize_text(r.get("id"))
            or text_q in normalize_text(r.get("category"))
            or text_q in normalize_text(r.get("type"))
            or text_q in normalize_text(r.get("name"))
            or text_q in normalize_text(r.get("station"))
        ]
    if since_dt:
        filtered_rows: list[dict] = []
        for row in filtered:
            row_dt = parse_iso_datetime(row.get("updated_at") or row.get("time"))
            if not row_dt:
                continue
            if row_dt >= since_dt:
                filtered_rows.append(row)
        filtered = filtered_rows

    if kind == "audit":
        action = normalize_text((query.get("action", [""])[0] or ""))
        if action:
            filtered = [r for r in filtered if action in normalize_text(r.get("action"))]

    return filtered


LIFECYCLE_ORDER = ["New", "Verified", "Assigned", "Resolved", "Solved", "Closed"]


def normalize_lifecycle(status: str | None) -> str:
    if not status:
        return "New"
    value = str(status).strip().title()
    return value if value in LIFECYCLE_ORDER else "New"


def append_audit(action: str, actor: str = "System") -> None:
    db = load_db()
    db["audit"].insert(0, {"action": action, "actor": actor, "time": datetime.now().isoformat(timespec="seconds")})
    db["audit"] = db["audit"][:300]
    save_db(db)


def build_dispatch_summary(db: dict) -> dict:
    cases = db.get("cases", [])
    now = datetime.now()
    open_cases = [c for c in cases if normalize_lifecycle(c.get("status")) != "Closed"]
    high_open = [c for c in open_cases if str(c.get("priority", "")).strip().title() == "High"]

    breach_count = 0
    for case in high_open:
        raw_time = case.get("time")
        case_time = None
        if isinstance(raw_time, str):
            try:
                case_time = datetime.fromisoformat(raw_time)
            except ValueError:
                case_time = None
        if case_time and (now - case_time).total_seconds() > 30 * 60:
            breach_count += 1

    status_counts = {k: 0 for k in LIFECYCLE_ORDER}
    for case in cases:
        status_counts[normalize_lifecycle(case.get("status"))] += 1

    return {
        "open_cases": len(open_cases),
        "high_priority_open": len(high_open),
        "sla_breaches": breach_count,
        "status_counts": status_counts,
    }


def build_station_workload(db: dict) -> list[dict]:
    stations = db.get("stations", [])
    cases = db.get("cases", [])
    rows: list[dict] = []
    for station in stations:
        name = station.get("name", "Unknown")
        total_officers = int(station.get("officers_total", 0) or 0)
        active_cases = sum(
            1
            for case in cases
            if normalize_lifecycle(case.get("status")) != "Closed"
            and str(case.get("station", "")).strip() == str(name)
        )
        available = max(total_officers - active_cases, 0)
        rows.append(
            {
                "station": name,
                "officers_total": total_officers,
                "active_cases": active_cases,
                "officers_available": available,
                "load": round(active_cases / total_officers, 2) if total_officers else 0,
            }
        )
    return rows


def build_health_details(db: dict) -> dict:
    latest_report = None
    if REPORT_FILE.exists():
        try:
            latest_report = json.loads(REPORT_FILE.read_text(encoding="utf-8")).get("generated_at")
        except Exception:
            latest_report = None

    return {
        "ok": True,
        "service": "crime-backend",
        "started_at": STARTED_AT.isoformat(timespec="seconds"),
        "uptime_seconds": int((datetime.now() - STARTED_AT).total_seconds()),
        "latest_report_generated_at": latest_report,
        "counts": {
            "users": len(db.get("users", [])),
            "complaints": len(db.get("complaints", [])),
            "cases": len(db.get("cases", [])),
            "watch": len(db.get("watch", [])),
            "feedback": len(db.get("feedback", [])),
            "cyber": len(db.get("cyber", [])),
            "cctv": len(db.get("cctv", [])),
            "audit": len(db.get("audit", [])),
        },
    }


def filter_complaints_by_district(db: dict, district: str, limit: int) -> list[dict]:
    """Filter complaints by district name (partial match)."""
    district_normalized = normalize_text(district)
    results: list[dict] = []
    
    for row in db.get("complaints", []):
        complaint_district = normalize_text(row.get("district") or "")
        # Check if search term is in district name
        if district_normalized in complaint_district or complaint_district in district_normalized:
            results.append({
                "source": "Complaint",
                "id": row.get("id", ""),
                "title": row.get("category") or "Unknown",
                "district": row.get("district") or "",
                "status": normalize_lifecycle(row.get("status")) if row else "NA",
                "time": row.get("updated_at") or row.get("time") or "",
            })
            if len(results) >= limit:
                return results
    
    return results


def build_quick_search(db: dict, query_text: str, limit: int) -> list[dict]:
    q = normalize_text(query_text)
    if not q:
        return []

    scope = [
        ("complaints", ["id", "category", "district", "name", "desc", "status"]),
        ("cases", ["id", "station", "officer", "notes", "status", "priority"]),
        ("watch", ["name", "area", "plan"]),
        ("cyber", ["type", "contact", "details"]),
        ("cctv", ["url"]),
    ]

    results: list[dict] = []
    for kind, keys in scope:
        for row in db.get(kind, []):
            haystack = " ".join(normalize_text(row.get(key)) for key in keys)
            if q not in haystack:
                continue
            results.append(
                {
                    "source": kind,
                    "id": row.get("id", ""),
                    "title": row.get("id") or row.get("category") or row.get("type") or row.get("name") or row.get("url") or "Record",
                    "district": row.get("district") or row.get("area") or row.get("station") or "",
                    "status": normalize_lifecycle(row.get("status")) if kind in {"complaints", "cases"} else "NA",
                    "time": row.get("updated_at") or row.get("time") or "",
                }
            )
            if len(results) >= limit:
                return results
    return results


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict | list) -> None:
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        etag = hashlib.sha1(raw_body).hexdigest()
        if self.headers.get("If-None-Match", "") == etag and status == 200:
            self.send_response(304)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, If-None-Match, Authorization")
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return

        use_gzip = "gzip" in (self.headers.get("Accept-Encoding", "").lower()) and len(raw_body) > 1024
        body = gzip.compress(raw_body) if use_gzip else raw_body

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, If-None-Match, Authorization")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("ETag", etag)
        self.send_header("Vary", "Accept-Encoding")
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _get_user_from_token(self, token: str) -> dict | None:
        if not token:
            return None
        db = load_db()
        return next((u for u in db.get("users", []) if u.get("token") == token), None)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            try:
                content = Path("hotspot_report.html").read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                return

        if path == "/api/health":
            self._send_json(200, {"ok": True, "service": "crime-backend"})
            return

        if path == "/api/health/details":
            db = load_db()
            self._send_json(200, build_health_details(db))
            return

        if path == "/api/report":
            if REPORT_FILE.exists():
                try:
                    payload = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
                except Exception:
                    payload = {"error": "Failed to parse report file"}
            else:
                payload = {"error": "Report file not found"}
            self._send_json(200, payload)
            return

        if path == "/api/dispatch/summary":
            db = load_db()
            self._send_json(200, build_dispatch_summary(db))
            return

        if path == "/api/metrics":
            db = load_db()
            payload = {
                "complaints": len(db.get("complaints", [])),
                "cases": len(db.get("cases", [])),
                "watch": len(db.get("watch", [])),
                "feedback": len(db.get("feedback", [])),
                "cyber": len(db.get("cyber", [])),
                "cctv": len(db.get("cctv", [])),
                "audit": len(db.get("audit", [])),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
            self._send_json(200, payload)
            return

        if path == "/api/stats":
            db = load_db()
            complaints = db.get("complaints", [])
            
            # Count by category
            categories = {}
            severity_stats = {"High": 0, "Medium": 0, "Low": 0}
            
            for complaint in complaints:
                category = complaint.get("category", "Other")
                categories[category] = categories.get(category, 0) + 1
                
                severity = complaint.get("ai_severity", "Low") or "Low"
                if severity in severity_stats:
                    severity_stats[severity] += 1
            
            payload = {
                "categoryLabels": list(categories.keys()),
                "categoryValues": list(categories.values()),
                "severityStats": severity_stats,
                "total": len(complaints)
            }
            self._send_json(200, payload)
            return

        if path == "/api/stations/workload":
            db = load_db()
            self._send_json(200, build_station_workload(db))
            return

        if path == "/api/complaints/status":
            query = parse_qs(parsed.query)
            complaint_id = (query.get("id", [""])[0] or "").strip()
            if not complaint_id:
                self._send_json(400, {"error": "Missing id"})
                return
            db = load_db()
            item = next((x for x in db.get("complaints", []) if str(x.get("id", "")) == complaint_id), None)
            if not item:
                self._send_json(404, {"error": "Complaint not found"})
                return
            self._send_json(200, {
                "id": complaint_id,
                "status": normalize_lifecycle(item.get("status")),
                "updated_by": item.get("updated_by", "System"),
                "updated_at": item.get("updated_at", item.get("time", "")),
                "remarks": item.get("remarks", ""),
            })
            return

        if path == "/api/search":
            query = parse_qs(parsed.query)
            q = (query.get("q", [""])[0] or "").strip()
            district_filter = (query.get("district", [""])[0] or "").strip()
            limit = parse_limit(query.get("limit", ["20"])[0], default=20, max_value=100)
            db = load_db()
            
            # If district is provided, filter by district
            if district_filter:
                rows = filter_complaints_by_district(db, district_filter, limit)
            elif q:
                rows = build_quick_search(db, q, limit)
            else:
                rows = []
            
            self._send_json(200, {"rows": rows, "meta": {"q": q, "district": district_filter, "count": len(rows), "limit": limit}})
            return

        db = load_db()
        route_map = {
            "/api/complaints": "complaints",
            "/api/cases": "cases",
            "/api/watch": "watch",
            "/api/feedback": "feedback",
            "/api/cyber": "cyber",
            "/api/cctv": "cctv",
            "/api/sos": "sos",
            "/api/audit": "audit",
        }

        if path in route_map:
            kind = route_map[path]
            query = parse_qs(parsed.query)
            limit = parse_limit(query.get("limit", ["200"])[0], default=200, max_value=500)
            offset = parse_offset(query.get("offset", ["0"])[0])
            rows = filter_rows(kind, db.get(kind, []), query)
            sliced = rows[offset : offset + limit]
            self._send_json(200, {
                "rows": sliced,
                "meta": {
                    "kind": kind,
                    "total": len(rows),
                    "limit": limit,
                    "offset": offset,
                    "count": len(sliced),
                },
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self._read_json()

        if path == "/api/complaints":
            token = self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            user = self._get_user_from_token(token)
            if not user and not payload.get("anonymous"):
                self._send_json(401, {"error": "Unauthorized. Please log in first."})
                return

            payload.setdefault("id", f"CMP-{int(datetime.now().timestamp())}")
            payload["status"] = normalize_lifecycle(payload.get("status"))
            if user and not payload.get("anonymous"):
                payload["user_id"] = user.get("id")
                payload["user_name"] = user.get("name")
            
            # Simple AI severity deduction
            desc = (payload.get("desc") or "").lower()
            category = (payload.get("category") or "").lower()
            severity = "Low"
            ai_score = 0.3
            if any(w in desc or w in category for w in ["murder", "rape", "gun", "shoot", "attack", "blood", "kill"]):
                severity = "High"
                ai_score = 0.95
            elif any(w in desc or w in category for w in ["steal", "rob", "theft", "break", "assault"]):
                severity = "Medium"
                ai_score = 0.65
            
            payload["ai_severity"] = severity
            payload["ai_confidence"] = ai_score

            item = append_item("complaints", payload, 200)
            actor_name = str(user.get("name") if (user and not payload.get("anonymous")) else "Citizen/Anonymous")
            append_audit(f"Complaint created: {item.get('id', 'NA')} (AI Severity: {severity})", actor_name)
            self._send_json(201, item)
            return

        if path == "/api/sos":
            # Emergency SOS Alert
            payload.setdefault("id", f"SOS-{int(datetime.now().timestamp())}")
            payload["status"] = "Active"
            payload.setdefault("sos_type", "Emergency")
            
            item = append_item("sos", payload, 100)
            append_audit(f"SOS Alert: {item.get('id', 'NA')} - {item.get('sos_type', 'Emergency')} at {item.get('location', 'Unknown')}", "Emergency")
            self._send_json(201, item)
            return

        if path == "/api/auth/register":
            name = str(payload.get("name", "")).strip()
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", "")).strip()
            role = str(payload.get("role", "citizen")).strip()
            if role not in ["citizen", "officer", "analyst"]:
                role = "citizen"
                
            if not name or not email or not password:
                self._send_json(400, {"error": "Missing name, email, or password"})
                return
            db = load_db()
            if any(u.get("email") == email for u in db.get("users", [])):
                self._send_json(400, {"error": "Email already registered"})
                return
            
            user_id = f"USR-{int(datetime.now().timestamp())}"
            # Simple hash for demo
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            token = hashlib.sha256(f"{user_id}-{datetime.now().timestamp()}".encode()).hexdigest()
            
            new_user = {
                "id": user_id,
                "name": name,
                "email": email,
                "password": hashed_pw,
                "token": token,
                "role": role,
                "created_at": datetime.now().isoformat(timespec="seconds")
            }
            db["users"].append(new_user)
            save_db(db)
            
            append_audit(f"User registered: {email}", name)
            
            # Return without password
            self._send_json(201, {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role,
                "token": token
            })
            return

        if path == "/api/auth/login":
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", "")).strip()
            
            db = load_db()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            
            for index, u in enumerate(db.get("users", [])):
                if u.get("email") == email and u.get("password") == hashed_pw:
                    # Gen new token
                    token = hashlib.sha256(f"{u.get('id')}-{datetime.now().timestamp()}".encode()).hexdigest()
                    u["token"] = token
                    db["users"][index] = u
                    save_db(db)
                    
                    append_audit(f"User logged in: {email}", u.get("name"))
                    self._send_json(200, {
                        "id": u.get("id"),
                        "name": u.get("name"),
                        "email": u.get("email"),
                        "role": u.get("role"),
                        "token": token
                    })
                    return
            
            self._send_json(401, {"error": "Invalid email or password"})
            return

        if path == "/api/admin/login":
            pin = str(payload.get("pin", "")).strip()
            # Demo hardcoded police PIN
            if pin == "4321":
                token = hashlib.sha256(f"admin-{datetime.now().timestamp()}".encode()).hexdigest()
                append_audit(f"Admin portal accessed", "Police/Admin")
                self._send_json(200, {
                    "id": "ADMIN-1",
                    "name": "Control Room Admin",
                    "role": "admin",
                    "token": token
                })
                return
            self._send_json(401, {"error": "Invalid admin PIN"})
            return

        if path == "/api/complaints/update-status":
            complaint_id = str(payload.get("id", "")).strip()
            if not complaint_id:
                self._send_json(400, {"error": "Missing id"})
                return
            status = normalize_lifecycle(payload.get("status"))
            actor = str(payload.get("actor", "Officer")).strip() or "Officer"
            remarks = str(payload.get("remarks", "")).strip()
            db = load_db()
            for complaint in db.get("complaints", []):
                if str(complaint.get("id", "")) == complaint_id:
                    complaint["status"] = status
                    complaint["updated_by"] = actor
                    complaint["updated_at"] = datetime.now().isoformat(timespec="seconds")
                    complaint["remarks"] = remarks
                    save_db(db)
                    append_audit(f"Complaint status updated: {complaint_id} -> {status}", actor)
                    self._send_json(200, complaint)
                    return
            self._send_json(404, {"error": "Complaint not found"})
            return

        if path == "/api/cases":
            payload["status"] = normalize_lifecycle(payload.get("status"))
            case_id = str(payload.get("id", "")).strip()
            item = append_item("cases", payload, 200)
            append_audit(f"Case created/updated: {item.get('id', 'NA')}", "Police")
            if case_id and payload["status"] in ["Resolved", "Closed", "Solved"]:
                db = load_db()
                for c in db.get("complaints", []):
                    c_id = str(c.get("id", "")).strip()
                    if c_id == case_id or c_id.endswith(case_id):
                        c["status"] = payload["status"]
                        c["updated_at"] = datetime.now().isoformat(timespec="seconds")
                for cy in db.get("cyber", []):
                    cy_id = str(cy.get("id", "")).strip()
                    if cy_id == case_id or cy_id.endswith(case_id):
                        cy["status"] = payload["status"]
                        cy["updated_at"] = datetime.now().isoformat(timespec="seconds")
                save_db(db)
            self._send_json(201, item)
            return

        if path == "/api/cases/update-status":
            case_id = str(payload.get("id", "")).strip()
            if not case_id:
                self._send_json(400, {"error": "Missing id"})
                return
            status = normalize_lifecycle(payload.get("status"))
            actor = str(payload.get("actor", "Officer")).strip() or "Officer"
            db = load_db()
            for case in db.get("cases", []):
                if str(case.get("id", "")) == case_id:
                    case["status"] = status
                    case["updated_by"] = actor
                    case["updated_at"] = datetime.now().isoformat(timespec="seconds")
                    if status in ["Resolved", "Closed", "Solved"]:
                        for c in db.get("complaints", []):
                            c_id = str(c.get("id", "")).strip()
                            if c_id == case_id or c_id.endswith(case_id):
                                c["status"] = status
                                c["updated_at"] = datetime.now().isoformat(timespec="seconds")
                        for cy in db.get("cyber", []):
                            cy_id = str(cy.get("id", "")).strip()
                            if cy_id == case_id or cy_id.endswith(case_id):
                                cy["status"] = status
                                cy["updated_at"] = datetime.now().isoformat(timespec="seconds")
                    save_db(db)
                    append_audit(f"Case status updated: {case_id} -> {status}", actor)
                    self._send_json(200, case)
                    return
            self._send_json(404, {"error": "Case not found"})
            return

        if path == "/api/watch":
            token = self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            user = self._get_user_from_token(token)
            if user:
                payload["user_id"] = user.get("id")
                payload["user_name"] = user.get("name")
            item = append_item("watch", payload, 100)
            self._send_json(201, item)
            return

        if path == "/api/feedback":
            token = self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            user = self._get_user_from_token(token)
            if user:
                payload["user_id"] = user.get("id")
                payload["user_name"] = user.get("name")
            item = append_item("feedback", payload, 150)
            self._send_json(201, item)
            return

        if path == "/api/cyber":
            token = self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            user = self._get_user_from_token(token)
            if user:
                payload["user_id"] = user.get("id")
                payload["user_name"] = user.get("name")
            item = append_item("cyber", payload, 150)
            self._send_json(201, item)
            return

        if path == "/api/cctv":
            token = self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            user = self._get_user_from_token(token)
            if not user or user.get("role") != "admin":
                 self._send_json(403, {"error": "Only admins can add CCTV feeds."})
                 return
            item = append_item("cctv", payload, 50)
            self._send_json(201, item)
            return

        if path == "/api/audit":
            item = append_item("audit", payload, 300)
            self._send_json(201, item)
            return

        if path == "/api/batch":
            operations = payload.get("operations", []) if isinstance(payload, dict) else []
            if not isinstance(operations, list) or not operations:
                self._send_json(400, {"error": "operations list required"})
                return

            endpoint_map = {
                "/complaints": ("complaints", 200),
                "/cases": ("cases", 200),
                "/watch": ("watch", 100),
                "/feedback": ("feedback", 150),
                "/cyber": ("cyber", 150),
                "/cctv": ("cctv", 50),
                "/audit": ("audit", 300),
            }
            db = load_db()
            results: list[dict] = []

            for op in operations[:100]:
                if not isinstance(op, dict):
                    continue
                op_path = str(op.get("path", "")).strip()
                op_payload = op.get("payload", {}) if isinstance(op.get("payload", {}), dict) else {}
                if op_path not in endpoint_map:
                    results.append({"path": op_path, "ok": False, "error": "unsupported path"})
                    continue

                kind, limit = endpoint_map[op_path]
                item = dict(op_payload)
                item.setdefault("time", datetime.now().isoformat(timespec="seconds"))
                if kind == "complaints":
                    item.setdefault("id", f"CMP-{int(datetime.now().timestamp())}")
                    item["status"] = normalize_lifecycle(item.get("status"))
                if kind == "cases":
                    item["status"] = normalize_lifecycle(item.get("status"))
                db[kind].insert(0, item)
                db[kind] = db[kind][:limit]
                results.append({"path": op_path, "ok": True, "id": item.get("id", "")})

            save_db(db)
            self._send_json(200, {"ok": True, "processed": len(results), "results": results})
            return

        self._send_json(404, {"error": "Not found"})


def main() -> None:
    host = "127.0.0.1"
    port = 5001
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Crime backend running at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
