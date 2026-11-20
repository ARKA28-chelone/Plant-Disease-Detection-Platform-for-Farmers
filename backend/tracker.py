"""
Plant health tracker helpers: turns a plant's health logs (and the user's
latest scan of that crop) into a trend and a short, rule-based recommendation.
"""
from backend.models import TrackedPlant, HealthLog, PredictionRecord

SYMPTOM_FIELDS = ["leaf_spots", "yellowing", "wilting", "pests"]


def log_to_dict(log: HealthLog) -> dict:
    return {
        "id": log.log_id,
        "health_score": log.health_score,
        "leaf_spots": bool(log.leaf_spots),
        "yellowing": bool(log.yellowing),
        "wilting": bool(log.wilting),
        "pests": bool(log.pests),
        "watered": bool(log.watered),
        "treated": bool(log.treated),
        "notes": log.notes or "",
        "logged_at": log.logged_at.isoformat() if log.logged_at else None,
    }


def health_trend(logs) -> str:
    """Compare the average of the last 3 logs with the 3 before them."""
    scores = [l.health_score for l in logs]
    if len(scores) < 2:
        return "new"
    recent = scores[-3:]
    earlier = scores[-6:-3] or scores[:1]
    diff = sum(recent) / len(recent) - sum(earlier) / len(earlier)
    if diff >= 0.5:
        return "improving"
    if diff <= -0.5:
        return "declining"
    return "stable"


def recommend(plant: TrackedPlant, latest_scan=None) -> str:
    """A short, practical tip based on the newest log, the trend and the latest scan."""
    logs = plant.logs
    if not logs:
        return "Add your first health log to start tracking this plant."

    last = logs[-1]
    trend = health_trend(logs)
    tips = []

    if latest_scan and "healthy" not in latest_scan.disease_name.lower():
        tips.append(f"Your latest scan showed {latest_scan.plant_name} {latest_scan.disease_name}; "
                    "follow its treatment plan in the PDF report.")
    if last.pests:
        tips.append("Pests spotted: inspect leaf undersides and try neem oil or insecticidal soap.")
    if last.leaf_spots and not last.treated:
        tips.append("Leaf spots without treatment: remove affected leaves and scan one to identify the disease.")
    if last.wilting and last.watered:
        tips.append("Wilting despite watering can mean root rot or wilt disease - check drainage and avoid overwatering.")
    elif last.wilting:
        tips.append("Wilting: water deeply at the soil line, ideally in the early morning.")
    if last.yellowing:
        tips.append("Yellowing leaves often point to nitrogen deficiency or overwatering - check soil moisture first.")

    if trend == "declining":
        tips.insert(0, "Health is declining over your recent logs - act soon and re-scan a leaf.")
    elif trend == "improving" and not tips:
        tips.append("Health is improving - keep up the current care routine.")

    if not tips:
        if last.health_score >= 4:
            tips.append("Plant looks healthy. Keep logging weekly to catch problems early.")
        else:
            tips.append("Health is below average with no clear symptom - scan a leaf to check for disease.")
    return " ".join(tips[:2])


def plant_summary(plant: TrackedPlant, db) -> dict:
    linked = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.tracked_id == plant.tracked_id)
        .order_by(PredictionRecord.created_at)
        .all()
    )
    # Prefer scans linked to this plant; otherwise fall back to the latest scan of the same crop
    latest_scan = linked[-1] if linked else (
        db.query(PredictionRecord)
        .filter(PredictionRecord.user_id == plant.user_id, PredictionRecord.plant_name == plant.crop)
        .order_by(PredictionRecord.created_at.desc())
        .first()
    )
    last = plant.logs[-1] if plant.logs else None
    return {
        "id": plant.tracked_id,
        "nickname": plant.nickname,
        "crop": plant.crop,
        "log_count": len(plant.logs),
        "latest_score": last.health_score if last else None,
        "last_logged": last.logged_at.isoformat() if last and last.logged_at else None,
        "trend": health_trend(plant.logs),
        "recommendation": recommend(plant, latest_scan),
        "logs": [log_to_dict(l) for l in plant.logs],
        "scans": [
            {"id": r.prediction_id, "disease": r.disease_name, "confidence": f"{r.confidence}%",
             "image_url": f"/uploads/{r.image_filename}", "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in linked
        ],
    }
