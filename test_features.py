"""Tests for the account features: feedback, notes, filters, linking, reminders, profile, export, admin."""
import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import User
from test_backend import create_sample_leaf_image

client = TestClient(app)


def new_user():
    """Fresh throwaway account so tests don't depend on each other."""
    email = f"t_{uuid.uuid4().hex[:10]}@example.com"
    res = client.post("/api/register", json={"name": "Feature Tester", "email": email, "password": "secret123"})
    assert res.status_code == 200
    return email, {"Authorization": "Bearer " + res.json()["token"]}


def scan(headers, tracked_id=None):
    data = {"selected_plant": "Tomato"}
    if tracked_id:
        data["tracked_id"] = str(tracked_id)
    res = client.post("/api/predict", headers=headers, data=data,
                      files={"image": ("leaf.jpg", create_sample_leaf_image(), "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()["prediction_id"]


def test_feedback_and_accuracy():
    _, h = new_user()
    a, b = scan(h), scan(h)
    assert client.post(f"/api/scans/{a}/feedback", headers=h, json={"is_correct": True}).status_code == 200
    res = client.post(f"/api/scans/{b}/feedback", headers=h, json={"is_correct": False, "correct_disease": "Leaf Mold"})
    assert res.json()["feedback"] == {"is_correct": False, "correct_disease": "Leaf Mold"}
    # Changing your mind updates the same row
    client.post(f"/api/scans/{b}/feedback", headers=h, json={"is_correct": True})
    fb = client.get("/api/me/summary", headers=h).json()["feedback"]
    assert fb == {"total": 2, "correct": 2, "accuracy": 100.0}


def test_notes_and_filters():
    _, h = new_user()
    sid = scan(h)
    res = client.patch(f"/api/scans/{sid}", headers=h, json={"notes": "Sprayed neem oil"})
    assert res.json()["notes"] == "Sprayed neem oil"
    assert client.get(f"/api/scans/{sid}", headers=h).json()["notes"] == "Sprayed neem oil"
    assert len(client.get("/api/history?q=neem", headers=h).json()) == 1
    assert client.get("/api/history?q=zzz", headers=h).json() == []
    plant = client.get(f"/api/scans/{sid}", headers=h).json()["plant"]  # model may override the chosen crop
    assert len(client.get(f"/api/history?plant={plant}&date_from=2000-01-01", headers=h).json()) == 1
    assert client.get("/api/history?plant=NoSuchPlant", headers=h).json() == []
    assert client.get("/api/history?date_from=bad", headers=h).status_code == 400
    assert plant in client.get("/api/history/filters", headers=h).json()["plants"]
    # Another user can't see or edit it
    _, other = new_user()
    assert client.get(f"/api/scans/{sid}", headers=other).status_code == 404
    assert client.patch(f"/api/scans/{sid}", headers=other, json={"notes": "x"}).status_code == 404


def test_link_scans_to_tracked_plant_and_plant_pdf():
    _, h = new_user()
    plant = client.post("/api/tracker", headers=h, json={"nickname": "Bed A", "crop": "Tomato"}).json()
    for days, score in [(3, 4), (1, 3)]:
        client.post(f"/api/tracker/{plant['id']}/logs", headers=h,
                    json={"health_score": score, "days_ago": days, "leaf_spots": True, "notes": "spots on lower leaves"})
    linked = scan(h, plant["id"])
    loose = scan(h)
    assert client.patch(f"/api/scans/{loose}", headers=h, json={"tracked_id": plant["id"]}).json()["tracked_name"] == "Bed A"
    summary = [p for p in client.get("/api/tracker", headers=h).json() if p["id"] == plant["id"]][0]
    assert {s["id"] for s in summary["scans"]} == {linked, loose}
    assert len(client.get(f"/api/history?tracked_id={plant['id']}", headers=h).json()) == 2

    pdf = client.get(f"/api/tracker/{plant['id']}/report", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    # Can't link to someone else's plant
    _, other = new_user()
    res = client.post("/api/predict", headers=other, data={"tracked_id": str(plant["id"])},
                      files={"image": ("leaf.jpg", create_sample_leaf_image(), "image/jpeg")})
    assert res.status_code == 404
    # Deleting the plant keeps its scans but unlinks them
    client.delete(f"/api/tracker/{plant['id']}", headers=h)
    assert client.get(f"/api/scans/{linked}", headers=h).json()["tracked_id"] is None


def test_scan_report_includes_notes():
    _, h = new_user()
    sid = scan(h)
    client.patch(f"/api/scans/{sid}", headers=h, json={"notes": "Applied copper spray"})
    assert client.get(f"/api/report/{sid}", headers=h).content.startswith(b"%PDF")


def test_reminders():
    _, h = new_user()
    sid = scan(h)
    r = client.post("/api/reminders", headers=h, json={"days": 7, "prediction_id": sid}).json()
    assert "Re-scan" in r["message"] and r["is_due"] is False
    assert client.post("/api/reminders", headers=h, json={"days": 0, "message": "x"}).status_code == 400
    assert client.post("/api/reminders", headers=h, json={"days": 3}).status_code == 400
    assert len(client.get("/api/reminders", headers=h).json()) == 1
    client.patch(f"/api/reminders/{r['id']}", headers=h, json={"done": True})
    assert client.get("/api/reminders", headers=h).json() == []
    assert len(client.get("/api/reminders?include_done=true", headers=h).json()) == 1


def test_profile_password_and_delete():
    email, h = new_user()
    assert client.patch("/api/me", headers=h, json={"name": "New Name"}).json()["name"] == "New Name"
    assert client.post("/api/me/password", headers=h,
                       json={"current_password": "wrong", "new_password": "newpass1"}).status_code == 400
    assert client.post("/api/me/password", headers=h,
                       json={"current_password": "secret123", "new_password": "newpass1"}).status_code == 200
    assert client.post("/api/login", json={"email": email, "password": "newpass1"}).status_code == 200
    scan(h)
    assert client.request("DELETE", "/api/me", headers=h, json={"password": "bad"}).status_code == 400
    assert client.request("DELETE", "/api/me", headers=h, json={"password": "newpass1"}).status_code == 200
    assert client.post("/api/login", json={"email": email, "password": "newpass1"}).status_code == 401


def test_csv_export():
    _, h = new_user()
    sid = scan(h)
    client.patch(f"/api/scans/{sid}", headers=h, json={"notes": "note, with comma"})
    res = client.get("/api/export/scans.csv", headers=h)
    assert res.status_code == 200 and "text/csv" in res.headers["content-type"]
    text = res.content.decode("utf-8-sig")
    assert text.startswith("scan_id,") and '"note, with comma"' in text
    assert client.get("/api/export/health-logs.csv", headers=h).status_code == 200


def test_admin_stats_requires_admin():
    email, h = new_user()
    assert client.get("/api/admin/stats", headers=h).status_code == 403
    db = SessionLocal()
    db.query(User).filter(User.email == email).update({"is_admin": 1})
    db.commit()
    db.close()
    stats = client.get("/api/admin/stats", headers=h).json()
    assert stats["totals"]["users"] >= 1 and len(stats["scans_per_day"]) == 14
    assert client.get("/api/me", headers=h).json()["is_admin"] is True


def test_alternatives_saved_with_scan():
    _, h = new_user()
    res = client.post("/api/predict", headers=h,
                      files={"image": ("leaf.jpg", create_sample_leaf_image(), "image/jpeg")}).json()
    alts = res["alternatives"]
    assert 1 <= len(alts) <= 3 and {"plant", "disease", "score"} <= set(alts[0])
    assert client.get(f"/api/scans/{res['prediction_id']}", headers=h).json()["alternatives"] == alts


def test_app_files_served():
    assert client.get("/manifest.json").json()["short_name"] == "PlantCare"
    assert client.get("/sw.js").headers["cache-control"] == "no-cache"
    assert client.get("/icons/icon-192.png").status_code == 200
    for page in ["batch.html", "compare.html", "offline.html"]:
        assert client.get(f"/{page}").status_code == 200
