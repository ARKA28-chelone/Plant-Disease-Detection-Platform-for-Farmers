import os
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response, RedirectResponse
from sqlalchemy.orm import Session

from backend.database import get_db, engine, Base
from pydantic import BaseModel
from typing import List
from datetime import timedelta
from backend.models import Plant, Disease, Treatment, PredictionRecord, User, TrackedPlant, HealthLog, Reminder
from backend.tracker import plant_summary
from backend import assistant
from backend.auth import hash_password, verify_password, create_token, get_optional_user, get_current_user
from backend.ml_engine import get_classifier
from backend.init_db import initialize_database
from backend.report import build_report
from backend.disease_data import get_disease_info
from backend.features import router as features_router

# Ensure database is ready
initialize_database()

app = FastAPI(
    title="Plant Disease Detection API",
    description="Machine Learning & DBMS backend for plant disease identification",
    version="1.0.0"
)

# Enable CORS for frontend requests (both localhost, 127.0.0.1, and local file:// origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(features_router)

_default_upload_dir = "/tmp/uploads" if os.getenv("VERCEL") else "uploads"
UPLOAD_DIR = os.path.abspath(os.getenv("UPLOAD_DIR", _default_upload_dir))
os.makedirs(UPLOAD_DIR, exist_ok=True)


from datetime import datetime, timezone

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _user_payload(user: User) -> dict:
    return {"id": user.user_id, "name": user.name, "email": user.email, "is_admin": bool(user.is_admin)}


@app.post("/api/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not req.name.strip() or "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid name and email.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(name=req.name.strip(), email=email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.user_id), "user": _user_payload(user)}


@app.post("/api/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"token": create_token(user.user_id), "user": _user_payload(user)}


@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return _user_payload(user)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/plants")
def get_plants(db: Session = Depends(get_db)):
    """Return all plants with their associated diseases from the database."""
    plants = db.query(Plant).all()
    response = []
    for p in plants:
        diseases = [d.name for d in p.diseases if "healthy" not in d.name.lower()]
        response.append({
            "id": p.plant_id,
            "name": p.name,
            "diseases": diseases
        })
    return response


@app.get("/api/diseases")
def get_diseases(db: Session = Depends(get_db)):
    """Return detailed disease descriptions and remedies."""
    diseases = db.query(Disease).all()
    results = []
    for d in diseases:
        treatments = [
            {"type": t.treatment_type, "recommendation": t.recommendation}
            for t in d.treatments
        ]
        results.append({
            "disease_id": d.disease_id,
            "plant": d.plant.name if d.plant else "Unknown",
            "name": d.name,
            "pathogen_type": d.pathogen_type,
            "symptoms": d.symptoms,
            "prevention": d.prevention,
            "treatments": treatments
        })
    return results


@app.post("/api/predict")
async def predict_plant_disease(
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    selected_plant: Optional[str] = Form(None),
    tracked_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Accepts leaf image via multipart/form-data ('image' or 'file'),
    and optional selected_plant (e.g., 'Tomato', 'Potato', 'Pepper', 'Corn').
    Runs the pre-trained Vision Transformer model, queries DBMS, logs prediction,
    and returns exact JSON format expected by script.js showResult(data).
    """
    upload = image or file
    # Optional link to one of the user's tracked plants
    if tracked_id:
        plant = db.get(TrackedPlant, tracked_id)
        if not user or not plant or plant.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="Tracked plant not found.")
    else:
        tracked_id = None
    if not upload:
        raise HTTPException(status_code=400, detail="No image file provided in request.")

    # Validation: Content-Type
    if upload.content_type and not upload.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type '{upload.content_type}'. Please upload a JPG or PNG image."
        )

    # Read bytes
    contents = await upload.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB.")

    # Save uploaded file
    file_ext = os.path.splitext(upload.filename)[1] if upload.filename else ".jpg"
    unique_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(saved_path, "wb") as f:
        f.write(contents)

    # Run ML Inference
    try:
        classifier = get_classifier()
        prediction = classifier.predict(contents, selected_plant=selected_plant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Inference failed: {str(e)}")

    # Top guesses in a readable form ("Tomato" / "Early Blight" / 97.5)
    alternatives = []
    for c in prediction.get("top_candidates", [])[:3]:
        info = get_disease_info(c["label"])
        alternatives.append({"plant": info["plant"], "disease": info["disease"], "score": c["score"]})

    # Store prediction log into database
    try:
        record = PredictionRecord(
            image_filename=unique_filename,
            predicted_label=prediction["raw_label"],
            plant_name=prediction["plant"],
            disease_name=prediction["disease_name"],
            confidence=prediction["confidence_value"],
            status="SUCCESS",
            user_id=user.user_id if user else None,
            tracked_id=tracked_id,
            candidates=json.dumps(alternatives)
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        prediction_id = record.prediction_id
    except Exception as db_err:
        db.rollback()
        print(f"Warning: Failed to save prediction to DB: {db_err}")
        prediction_id = None

    # Return structure directly matching script.js expectations
    return {
        "status": "success",
        "prediction_id": prediction_id,
        "plant": prediction["plant"],
        "disease": prediction["disease"],                 # Used by script.js: resDisease
        "confidence": prediction["confidence"],           # Used by script.js: resConfidence
        "info": prediction["info"],                       # Used by script.js: resInfo
        "details": prediction["details"],
        "warning_note": prediction.get("warning_note"),
        "top_candidates": prediction["top_candidates"],
        "alternatives": alternatives,
        "image_url": f"/uploads/{unique_filename}"
    }


@app.get("/api/report/{prediction_id}")
def download_report(prediction_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Generate the PDF Plant Health Report for one of the user's scans."""
    record = db.get(PredictionRecord, prediction_id)
    if not record or record.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Scan not found.")
    pdf_bytes = build_report(record, user, UPLOAD_DIR)
    filename = f"PlantCare_Report_{record.plant_name}_{record.prediction_id}.pdf".replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------- Plant health tracker ----------

class TrackedPlantRequest(BaseModel):
    nickname: str
    crop: str


class HealthLogRequest(BaseModel):
    health_score: int
    leaf_spots: bool = False
    yellowing: bool = False
    wilting: bool = False
    pests: bool = False
    watered: bool = False
    treated: bool = False
    notes: Optional[str] = None
    days_ago: int = 0   # lets farmers back-fill a log for an earlier day


def _get_owned_plant(tracked_id: int, user: User, db: Session) -> TrackedPlant:
    plant = db.get(TrackedPlant, tracked_id)
    if not plant or plant.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Plant not found.")
    return plant


@app.get("/api/tracker")
def list_tracked_plants(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plants = db.query(TrackedPlant).filter(TrackedPlant.user_id == user.user_id).order_by(TrackedPlant.created_at).all()
    return [plant_summary(p, db) for p in plants]


@app.post("/api/tracker")
def add_tracked_plant(req: TrackedPlantRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not req.nickname.strip() or not req.crop.strip():
        raise HTTPException(status_code=400, detail="Please enter a name and crop.")
    plant = TrackedPlant(user_id=user.user_id, nickname=req.nickname.strip()[:100], crop=req.crop.strip()[:100])
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant_summary(plant, db)


@app.delete("/api/tracker/{tracked_id}")
def delete_tracked_plant(tracked_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plant = _get_owned_plant(tracked_id, user, db)
    # Keep the scans and reminders, just unlink them from the removed plant
    db.query(PredictionRecord).filter(PredictionRecord.tracked_id == plant.tracked_id).update({"tracked_id": None})
    db.query(Reminder).filter(Reminder.tracked_id == plant.tracked_id).update({"tracked_id": None})
    db.delete(plant)
    db.commit()
    return {"status": "deleted"}


@app.post("/api/tracker/{tracked_id}/logs")
def add_health_log(tracked_id: int, req: HealthLogRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plant = _get_owned_plant(tracked_id, user, db)
    if not 1 <= req.health_score <= 5:
        raise HTTPException(status_code=400, detail="Health score must be between 1 and 5.")
    log = HealthLog(
        tracked_id=plant.tracked_id,
        health_score=req.health_score,
        leaf_spots=int(req.leaf_spots), yellowing=int(req.yellowing), wilting=int(req.wilting),
        pests=int(req.pests), watered=int(req.watered), treated=int(req.treated),
        notes=(req.notes or "").strip()[:1000] or None,
        logged_at=datetime.now(timezone.utc) - timedelta(days=max(0, min(req.days_ago, 365))),
    )
    db.add(log)
    db.commit()
    db.refresh(plant)
    return plant_summary(plant, db)


@app.delete("/api/tracker/{tracked_id}/logs/{log_id}")
def delete_health_log(tracked_id: int, log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plant = _get_owned_plant(tracked_id, user, db)
    log = db.get(HealthLog, log_id)
    if not log or log.tracked_id != plant.tracked_id:
        raise HTTPException(status_code=404, detail="Log not found.")
    db.delete(log)
    db.commit()
    db.refresh(plant)
    return plant_summary(plant, db)


# ---------- Farmer AI assistant ----------

class ChatTurn(BaseModel):
    role: str
    content: str


class AssistantRequest(BaseModel):
    message: str
    history: List[ChatTurn] = []
    language: str = "en"   # "hi" asks the assistant to reply in Hindi


@app.post("/api/assistant")
def ask_assistant(req: AssistantRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    question = req.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please type a question.")
    return assistant.ask(question[:2000], [t.model_dump() for t in req.history], db, user, req.language)


# Mount uploads directory to serve uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/icons", StaticFiles(directory=os.path.join(PROJECT_ROOT, "icons")), name="icons")

PAGES = ["index.html", "login.html", "dashboard.html", "results.html", "tracker.html", "assistant.html",
         "diseases.html", "profile.html", "admin.html", "batch.html", "compare.html", "offline.html"]

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(PROJECT_ROOT, "index.html"))

@app.get("/dashoard.html")
def redirect_old_dashboard():
    # The page used to be misspelled; keep old links working
    return RedirectResponse("/dashboard.html")

@app.get("/auth.js")
def serve_auth_js():
    return FileResponse(os.path.join(PROJECT_ROOT, "auth.js"))

@app.get("/manifest.json")
def serve_manifest():
    return FileResponse(os.path.join(PROJECT_ROOT, "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js")
def serve_service_worker():
    # Never cache the worker itself so updates are picked up immediately
    return FileResponse(os.path.join(PROJECT_ROOT, "sw.js"), media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})

@app.get("/upload-tools.js")
def serve_upload_tools_js():
    return FileResponse(os.path.join(PROJECT_ROOT, "upload-tools.js"))

@app.get("/i18n.js")
def serve_i18n_js():
    return FileResponse(os.path.join(PROJECT_ROOT, "i18n.js"))

@app.get("/chat-widget.js")
def serve_chat_widget_js():
    return FileResponse(os.path.join(PROJECT_ROOT, "chat-widget.js"))

def _page_route(name):
    def serve():
        return FileResponse(os.path.join(PROJECT_ROOT, name))
    return serve

for _page in PAGES:
    app.add_api_route(f"/{_page}", _page_route(_page), methods=["GET"], include_in_schema=False)

@app.get("/style.css")
def serve_css():
    return FileResponse(os.path.join(PROJECT_ROOT, "style.css"))

@app.get("/script.js")
def serve_js():
    return FileResponse(os.path.join(PROJECT_ROOT, "script.js"))
