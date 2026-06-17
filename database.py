"""Database layer with SQLAlchemy — supports SQLite and PostgreSQL.

Usage:
  DATABASE_URL=postgresql://user:pass@host/db  # uses PostgreSQL
  DATABASE_URL=sqlite:///bot_data.db            # uses SQLite (fallback)
"""
from __future__ import annotations

import json
import os
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, JSON, create_engine, event,
    text as sa_text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

PROJECT_DIR = Path(__file__).parent
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{PROJECT_DIR / 'bot_data.db'}",
)

# Fix for Railway's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Enable WAL mode for SQLite
if "sqlite" in DATABASE_URL:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


# ── Models ──

class StudentModel(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    level = Column(String(50), default="")
    city = Column(String(100), default="")
    booking_datetime = Column(String(50), default="")
    status = Column(String(50), default="pending")
    result_json = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LogModel(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_key = Column(String(255), default="")
    level = Column(String(50), default="")
    message = Column(Text, default="")
    time = Column(DateTime, default=datetime.utcnow)


class StateModel(Base):
    __tablename__ = "bot_state"
    key = Column(String(255), primary_key=True)
    value = Column(Text, default="")


class SessionModel(Base):
    __tablename__ = "sessions"
    session_id = Column(String(255), primary_key=True)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class QueueHistoryModel(Base):
    __tablename__ = "queue_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    level = Column(String(50), default="")
    city = Column(String(100), default="")
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=0)
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    result_json = Column(Text, default="")


class AuditLogModel(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    details = Column(Text, default="")
    ip = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Initialization ──

def init_db():
    Base.metadata.create_all(bind=engine)


# ── Session management ──

def create_session(email: str, expiry_hours: int = 24) -> str:
    session_id = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    with SessionLocal() as session:
        s = SessionModel(session_id=session_id, email=email, expires_at=expires_at)
        session.add(s)
        session.commit()
    return session_id


def validate_session(session_id: str) -> Optional[str]:
    with SessionLocal() as session:
        s = session.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.expires_at > datetime.utcnow(),
        ).first()
        return s.email if s else None


def delete_session(session_id: str):
    with SessionLocal() as session:
        session.query(SessionModel).filter(SessionModel.session_id == session_id).delete()
        session.commit()


def cleanup_expired_sessions():
    with SessionLocal() as session:
        session.query(SessionModel).filter(SessionModel.expires_at <= datetime.utcnow()).delete()
        session.commit()


# ── State management ──

def set_state(key: str, value: str):
    with SessionLocal() as session:
        existing = session.query(StateModel).filter(StateModel.key == key).first()
        if existing:
            existing.value = value
        else:
            session.add(StateModel(key=key, value=value))
        session.commit()


def get_state(key: str, default: str = "") -> str:
    with SessionLocal() as session:
        row = session.query(StateModel).filter(StateModel.key == key).first()
        return row.value if row else default


def delete_state(key: str):
    with SessionLocal() as session:
        session.query(StateModel).filter(StateModel.key == key).delete()
        session.commit()


# ── Checkpoint management ──

def save_checkpoint(booking_key: str, sequence_id: int, url: str):
    set_state(f"checkpoint_{booking_key}", json.dumps({"seq": sequence_id, "url": url}))


def get_checkpoint(booking_key: str) -> Optional[Dict]:
    raw = get_state(f"checkpoint_{booking_key}")
    if raw:
        return json.loads(raw)
    return None


def clear_checkpoint(booking_key: str):
    delete_state(f"checkpoint_{booking_key}")


def clear_all_checkpoints():
    with SessionLocal() as session:
        session.query(StateModel).filter(StateModel.key.like("checkpoint_%")).delete()
        session.commit()


# ── Student management ──

def save_students(students: List[Dict]):
    with SessionLocal() as session:
        session.query(StudentModel).delete()
        for s in students:
            session.add(StudentModel(
                name=s.get("name", ""),
                email=s.get("email", ""),
                level=s.get("level", ""),
                city=s.get("city", ""),
                booking_datetime=s.get("booking_datetime", ""),
                status=s.get("status", "pending"),
                result_json=json.dumps(s.get("result", {})),
            ))
        session.commit()


def get_students() -> List[Dict]:
    with SessionLocal() as session:
        rows = session.query(StudentModel).order_by(StudentModel.id).all()
        return [{
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "level": r.level,
            "city": r.city,
            "booking_datetime": r.booking_datetime,
            "status": r.status,
            "result": json.loads(r.result_json) if r.result_json else {},
        } for r in rows]


def update_student_status(student_id: int, status: str, result: Optional[Dict] = None):
    with SessionLocal() as session:
        student = session.query(StudentModel).filter(StudentModel.id == student_id).first()
        if student:
            student.status = status
            if result:
                student.result_json = json.dumps(result)
            session.commit()


# ── Log management ──

def add_log(student_key: str, level: str, message: str):
    with SessionLocal() as session:
        session.add(LogModel(student_key=str(student_key), level=level, message=str(message)))
        session.commit()


def get_logs(limit: int = 100, date_filter: Optional[str] = None) -> List[Dict]:
    with SessionLocal() as session:
        q = session.query(LogModel).order_by(LogModel.id.desc())
        if date_filter:
            from datetime import datetime as dt, timedelta
            try:
                d = dt.strptime(date_filter, "%Y-%m-%d")
                q = q.filter(LogModel.time >= d).filter(LogModel.time < d + timedelta(days=1))
            except ValueError:
                pass
        rows = q.limit(limit).all()
        return [{
            "time": r.time.isoformat() if r.time else "",
            "student_key": r.student_key,
            "level": r.level,
            "message": r.message,
        } for r in rows]


def search_logs(query: str, limit: int = 100) -> List[Dict]:
    with SessionLocal() as session:
        q = session.query(LogModel).order_by(LogModel.id.desc())
        q = q.filter(
            LogModel.student_key.ilike(f"%{query}%") |
            LogModel.message.ilike(f"%{query}%")
        )
        rows = q.limit(limit).all()
        return [{
            "time": r.time.isoformat() if r.time else "",
            "student_key": r.student_key,
            "level": r.level,
            "message": r.message,
        } for r in rows]


def get_booking_history(limit: int = 100) -> List[Dict]:
    """Combine queue history + recent logs as a unified booking history."""
    with SessionLocal() as session:
        qh = session.query(QueueHistoryModel).order_by(QueueHistoryModel.finished_at.desc().nullsfirst()).limit(limit).all()
        rows = [{
            "type": "booking",
            "name": r.name,
            "email": r.email,
            "level": r.level,
            "city": r.city,
            "status": r.status,
            "result": json.loads(r.result_json) if r.result_json else {},
            "queued_at": r.queued_at.isoformat() if r.queued_at else "",
            "finished_at": r.finished_at.isoformat() if r.finished_at else "",
        } for r in qh]
        return rows


# ── Audit log ──

def add_audit_log(action: str, email: str, details: str = "", ip: str = ""):
    with SessionLocal() as session:
        session.add(AuditLogModel(action=action, email=email, details=details, ip=ip))
        session.commit()


def get_audit_logs(limit: int = 100) -> List[Dict]:
    with SessionLocal() as session:
        rows = session.query(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(limit).all()
        return [{
            "id": r.id,
            "action": r.action,
            "email": r.email,
            "details": r.details,
            "ip": r.ip,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        } for r in rows]


# ── Queue history ──

def save_queue_history(items: List[Dict]):
    with SessionLocal() as session:
        session.query(QueueHistoryModel).delete()
        for item in items:
            session.add(QueueHistoryModel(
                name=item.get("name", ""),
                email=item.get("email", ""),
                level=item.get("level", ""),
                city=item.get("city", ""),
                status=item.get("status", "pending"),
                priority=item.get("priority", 0),
                result_json=json.dumps(item.get("result", {})),
            ))
        session.commit()


def get_queue_history(limit: int = 100) -> List[Dict]:
    with SessionLocal() as session:
        rows = session.query(QueueHistoryModel).order_by(QueueHistoryModel.id.desc()).limit(limit).all()
        return [{
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "level": r.level,
            "city": r.city,
            "status": r.status,
            "priority": r.priority,
            "queued_at": r.queued_at.isoformat() if r.queued_at else "",
            "started_at": r.started_at.isoformat() if r.started_at else "",
            "finished_at": r.finished_at.isoformat() if r.finished_at else "",
            "result": json.loads(r.result_json) if r.result_json else {},
        } for r in rows]
