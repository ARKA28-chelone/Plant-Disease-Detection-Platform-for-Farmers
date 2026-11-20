"""
Account-level features: scan history/filters, scan notes + plant linking, prediction
feedback, profile management, reminders, CSV export, tracked-plant PDF and admin stats.
"""
import io
import os
import json
import csv
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.auth import get_current_user, hash_password, verify_password
from backend.database import get_db
from backend.models import (User, PredictionRecord, PredictionFeedback, TrackedPlant,
                            HealthLog, Reminder, Disease)
from backend.report import build_plant_report

router = APIRouter()
UPLOAD_DIR = os.path.abspath(os.getenv("UPLOAD_DIR", "uploads"))


def _iso(dt):
    return dt.isoformat() if dt else None


def _now():
    # SQLite stores naive datetimes; keep everything as naive UTC
    return datetime.now(timezone.utc).replace(tzinfo=None)


def scan_to_dict(r: PredictionRecord, plant_names: Optional[dict] = None) -> dict:
    fb = r.feedback
    return {
        "id": r.prediction_id,
        "filename": r.image_filename,
        "image_url": f"/uploads/{r.image_filename}",
        "plant": r.plant_name,
        "disease": r.disease_name,
        "confidence": f"{r.confidence}%",
        "created_at": _iso(r.created_at),
        "notes": r.notes or "",
        "tracked_id": r.tracked_id,
        "tracked_name": (plant_names or {}).get(r.tracked_id),
        "feedback": None if not fb else {"is_correct": bool(fb.is_correct), "correct_disease": fb.correct_disease},
        "alternatives": json.loads(r.candidates) if r.candidates else [],
    }


def _owned_scan(prediction_id: int, user: User, db: Session) -> PredictionRecord:
    record = db.get(PredictionRecord, prediction_id)
    if not record or record.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return record


def _owned_plant(tracked_id: int, user: User, db: Session) -> TrackedPlant:
    plant = db.get(TrackedPlant, tracked_id)
    if not plant or plant.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Plant not found.")
    return plant


def _plant_names(user: User, db: Session) -> dict:
    return {p.tracked_id: p.nickname for p in db.query(TrackedPlant).filter(TrackedPlant.user_id == user.user_id)}


def _parse_date(value: Optional[str], field: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} must be a date like 2026-10-27.")


# ---------- Scan history with search & filters ----------

@router.get("/api/history")
def get_prediction_history(
    limit: int = Query(20, ge=1, le=500),
    plant: Optional[str] = None,
    disease: Optional[str] = None,
    q: Optional[str] = None,
    diseased_only: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tracked_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the logged-in user's past scans, optionally filtered."""
    query = db.query(PredictionRecord).filter(PredictionRecord.user_id == user.user_id)
    if plant:
        query = query.filter(PredictionRecord.plant_name == plant)
    if disease:
        query = query.filter(PredictionRecord.disease_name == disease)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter((PredictionRecord.disease_name.ilike(like)) |
                             (PredictionRecord.plant_name.ilike(like)) |
                             (PredictionRecord.notes.ilike(like)))
    if diseased_only:
        query = query.filter(~PredictionRecord.disease_name.ilike("%healthy%"))
    start, end = _parse_date(date_from, "date_from"), _parse_date(date_to, "date_to")
    if start:
        query = query.filter(PredictionRecord.created_at >= start)
    if end:
        query = query.filter(PredictionRecord.created_at < end + timedelta(days=1))
    if tracked_id:
        query = query.filter(PredictionRecord.tracked_id == tracked_id)
    records = query.order_by(PredictionRecord.created_at.desc()).limit(limit).all()
    names = _plant_names(user, db)
    return [scan_to_dict(r, names) for r in records]


@router.get("/api/history/filters")
def history_filter_options(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Distinct plants/diseases the user has scanned, for the filter dropdowns."""
    rows = (db.query(PredictionRecord.plant_name, PredictionRecord.disease_name)
            .filter(PredictionRecord.user_id == user.user_id).distinct().all())
    return {"plants": sorted({r[0] for r in rows}), "diseases": sorted({r[1] for r in rows})}


# ---------- Single scan: details, notes, plant link, feedback ----------

class ScanUpdate(BaseModel):
    notes: Optional[str] = None
    tracked_id: Optional[int] = None   # 0 unlinks the scan


@router.get("/api/scans/{prediction_id}")
def get_scan(prediction_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return scan_to_dict(_owned_scan(prediction_id, user, db), _plant_names(user, db))


@router.patch("/api/scans/{prediction_id}")
def update_scan(prediction_id: int, req: ScanUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = _owned_scan(prediction_id, user, db)
    if req.notes is not None:
        record.notes = req.notes.strip()[:2000] or None
    if req.tracked_id is not None:
        record.tracked_id = _owned_plant(req.tracked_id, user, db).tracked_id if req.tracked_id else None
    db.commit()
    return scan_to_dict(record, _plant_names(user, db))


class FeedbackRequest(BaseModel):
    is_correct: bool
    correct_disease: Optional[str] = None


@router.post("/api/scans/{prediction_id}/feedback")
def give_feedback(prediction_id: int, req: FeedbackRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = _owned_scan(prediction_id, user, db)
    fb = record.feedback or PredictionFeedback(prediction_id=record.prediction_id)
    fb.is_correct = int(req.is_correct)
    fb.correct_disease = None if req.is_correct else ((req.correct_disease or "").strip()[:150] or None)
    fb.created_at = _now()
    db.add(fb)
    db.commit()
    db.refresh(record)
    return scan_to_dict(record, _plant_names(user, db))


def _accuracy(feedback_rows) -> dict:
    total = len(feedback_rows)
    correct = sum(1 for f in feedback_rows if f.is_correct)
    return {"total": total, "correct": correct, "accuracy": round(correct / total * 100, 1) if total else None}


# ---------- Profile ----------

class ProfileUpdate(BaseModel):
    name: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class DeleteAccount(BaseModel):
    password: str


@router.get("/api/me/summary")
def my_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    feedback = (db.query(PredictionFeedback).join(PredictionRecord)
                .filter(PredictionRecord.user_id == user.user_id).all())
    plant_ids = [p.tracked_id for p in db.query(TrackedPlant).filter(TrackedPlant.user_id == user.user_id)]
    return {
        "name": user.name,
        "email": user.email,
        "is_admin": bool(user.is_admin),
        "member_since": _iso(user.created_at),
        "scan_count": db.query(PredictionRecord).filter(PredictionRecord.user_id == user.user_id).count(),
        "tracked_count": len(plant_ids),
        "log_count": db.query(HealthLog).filter(HealthLog.tracked_id.in_(plant_ids)).count() if plant_ids else 0,
        "feedback": _accuracy(feedback),
    }


@router.patch("/api/me")
def update_profile(req: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    user.name = name[:100]
    db.commit()
    return {"id": user.user_id, "name": user.name, "email": user.email, "is_admin": bool(user.is_admin)}


@router.post("/api/me/password")
def change_password(req: PasswordChange, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"status": "Password updated."}


@router.delete("/api/me")
def delete_account(req: DeleteAccount, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Permanently delete the account with all its scans, images, plants, logs and reminders."""
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Password is incorrect.")
    scans = db.query(PredictionRecord).filter(PredictionRecord.user_id == user.user_id).all()
    filenames = [s.image_filename for s in scans]
    db.query(Reminder).filter(Reminder.user_id == user.user_id).delete()
    for s in scans:
        db.delete(s)   # cascades to feedback
    for p in db.query(TrackedPlant).filter(TrackedPlant.user_id == user.user_id).all():
        db.delete(p)   # cascades to health logs
    db.delete(user)
    db.commit()
    for name in filenames:
        try:
            os.remove(os.path.join(UPLOAD_DIR, name))
        except OSError:
            pass
    return {"status": "Account deleted."}


# ---------- Reminders ----------

class ReminderRequest(BaseModel):
    days: int = 7
    message: Optional[str] = None
    prediction_id: Optional[int] = None
    tracked_id: Optional[int] = None


class ReminderUpdate(BaseModel):
    done: bool


def _reminder_dict(r: Reminder) -> dict:
    return {
        "id": r.reminder_id,
        "message": r.message,
        "due_at": _iso(r.due_at),
        "is_due": r.due_at <= _now(),
        "done": bool(r.done),
        "prediction_id": r.prediction_id,
        "tracked_id": r.tracked_id,
    }


@router.get("/api/reminders")
def list_reminders(include_done: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Reminder).filter(Reminder.user_id == user.user_id)
    if not include_done:
        query = query.filter(Reminder.done == 0)
    return [_reminder_dict(r) for r in query.order_by(Reminder.due_at).all()]


@router.post("/api/reminders")
def create_reminder(req: ReminderRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not 1 <= req.days <= 90:
        raise HTTPException(status_code=400, detail="Reminder must be between 1 and 90 days away.")
    message = (req.message or "").strip()
    if req.prediction_id:
        scan = _owned_scan(req.prediction_id, user, db)
        message = message or f"Re-scan your {scan.plant_name} ({scan.disease_name}) to check recovery."
    if req.tracked_id:
        plant = _owned_plant(req.tracked_id, user, db)
        message = message or f"Check on {plant.nickname} and log its health."
    if not message:
        raise HTTPException(status_code=400, detail="Please enter a reminder message.")
    reminder = Reminder(user_id=user.user_id, prediction_id=req.prediction_id, tracked_id=req.tracked_id,
                        message=message[:255], due_at=_now() + timedelta(days=req.days))
    db.add(reminder)
    db.commit()
    return _reminder_dict(reminder)


@router.patch("/api/reminders/{reminder_id}")
def update_reminder(reminder_id: int, req: ReminderUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    reminder.done = int(req.done)
    db.commit()
    return _reminder_dict(reminder)


@router.delete("/api/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    db.delete(reminder)
    db.commit()
    return {"status": "deleted"}


# ---------- CSV export ----------

def _csv_response(header, rows, filename):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    # BOM so Excel opens UTF-8 correctly
    return Response(content="﻿" + buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/api/export/scans.csv")
def export_scans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    names = _plant_names(user, db)
    records = (db.query(PredictionRecord).filter(PredictionRecord.user_id == user.user_id)
               .order_by(PredictionRecord.created_at).all())
    rows = []
    for r in records:
        fb = r.feedback
        rows.append([
            r.prediction_id, r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
            r.plant_name, r.disease_name, f"{r.confidence:.2f}", names.get(r.tracked_id, ""),
            "" if not fb else ("correct" if fb.is_correct else "wrong"),
            (fb.correct_disease or "") if fb else "", r.notes or "",
        ])
    return _csv_response(["scan_id", "date_utc", "plant", "predicted_disease", "confidence_percent",
                          "tracked_plant", "feedback", "actual_disease", "notes"], rows, "plantcare_scans.csv")


@router.get("/api/export/health-logs.csv")
def export_health_logs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = []
    for p in db.query(TrackedPlant).filter(TrackedPlant.user_id == user.user_id).order_by(TrackedPlant.tracked_id):
        for l in p.logs:
            rows.append([p.nickname, p.crop, l.logged_at.strftime("%Y-%m-%d") if l.logged_at else "",
                         l.health_score, *("yes" if getattr(l, f) else "no" for f in
                                           ("leaf_spots", "yellowing", "wilting", "pests", "watered", "treated")),
                         l.notes or ""])
    return _csv_response(["plant", "crop", "date", "health_score", "leaf_spots", "yellowing", "wilting",
                          "pests", "watered", "treated", "notes"], rows, "plantcare_health_logs.csv")


# ---------- Tracked plant PDF summary ----------

@router.get("/api/tracker/{tracked_id}/report")
def tracked_plant_report(tracked_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plant = _owned_plant(tracked_id, user, db)
    scans = (db.query(PredictionRecord).filter(PredictionRecord.tracked_id == plant.tracked_id)
             .order_by(PredictionRecord.created_at).all())
    from backend.tracker import plant_summary
    pdf = build_plant_report(plant, plant_summary(plant, db), scans, user, UPLOAD_DIR)
    filename = f"PlantCare_{plant.nickname}_Summary.pdf".replace(" ", "_")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ---------- Admin ----------

def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only.")
    return user


@router.get("/api/admin/stats")
def admin_stats(days: int = Query(14, ge=7, le=90), db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    since = _now() - timedelta(days=days - 1)
    since = since.replace(hour=0, minute=0, second=0, microsecond=0)
    recent = db.query(PredictionRecord.created_at).filter(PredictionRecord.created_at >= since).all()
    per_day = Counter(r[0].strftime("%Y-%m-%d") for r in recent if r[0])
    day_list = [(since + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    top = (db.query(PredictionRecord.plant_name, PredictionRecord.disease_name, func.count().label("n"))
           .filter(~PredictionRecord.disease_name.ilike("%healthy%"))
           .group_by(PredictionRecord.plant_name, PredictionRecord.disease_name)
           .order_by(func.count().desc()).limit(8).all())
    by_plant = (db.query(PredictionRecord.plant_name, func.count())
                .group_by(PredictionRecord.plant_name).order_by(func.count().desc()).all())
    users = db.query(User).order_by(User.created_at.desc()).all()
    scan_counts = dict(db.query(PredictionRecord.user_id, func.count()).group_by(PredictionRecord.user_id).all())

    return {
        "totals": {
            "users": len(users),
            "scans": db.query(PredictionRecord).count(),
            "guest_scans": db.query(PredictionRecord).filter(PredictionRecord.user_id.is_(None)).count(),
            "tracked_plants": db.query(TrackedPlant).count(),
            "health_logs": db.query(HealthLog).count(),
            "diseases_in_db": db.query(Disease).count(),
        },
        "feedback": _accuracy(db.query(PredictionFeedback).all()),
        "scans_per_day": [{"date": d, "count": per_day.get(d, 0)} for d in day_list],
        "top_diseases": [{"plant": p, "disease": d, "count": n} for p, d, n in top],
        "scans_by_plant": [{"plant": p, "count": n} for p, n in by_plant],
        "users": [{"name": u.name, "email": u.email, "joined": _iso(u.created_at),
                   "scans": scan_counts.get(u.user_id, 0), "is_admin": bool(u.is_admin)} for u in users[:20]],
    }
