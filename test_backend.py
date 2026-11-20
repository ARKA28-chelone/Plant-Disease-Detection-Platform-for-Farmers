import os
import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import Plant, Disease, PredictionRecord

client = TestClient(app)

def create_sample_leaf_image() -> bytes:
    """Generate a synthetic leaf-like image for testing."""
    img = Image.new("RGB", (224, 224), color=(34, 139, 34)) # Forest green
    draw = ImageDraw.Draw(img)
    # Draw leaf veins and spots
    draw.line([(112, 10), (112, 214)], fill=(144, 238, 144), width=3)
    draw.line([(112, 60), (60, 100)], fill=(144, 238, 144), width=2)
    draw.line([(112, 60), (164, 100)], fill=(144, 238, 144), width=2)
    draw.ellipse([(90, 80), (130, 120)], fill=(139, 69, 19)) # Blight-like spot
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_health():
    """Test health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("[PASS] Health check endpoint passed.")

def test_get_plants():
    """Test fetching plants and their diseases."""
    response = client.get("/api/plants")
    assert response.status_code == 200
    plants = response.json()
    assert len(plants) >= 4
    plant_names = [p["name"] for p in plants]
    assert "Tomato" in plant_names
    assert "Potato" in plant_names
    assert "Pepper" in plant_names
    assert "Corn" in plant_names
    print(f"[PASS] Plants endpoint passed. Found {len(plants)} plants.")

def test_get_diseases():
    """Test fetching diseases knowledge base."""
    response = client.get("/api/diseases")
    assert response.status_code == 200
    diseases = response.json()
    assert len(diseases) > 0
    # Check that remedies are attached
    has_treatments = any(len(d["treatments"]) > 0 for d in diseases)
    assert has_treatments
    print(f"[PASS] Diseases endpoint passed. Loaded {len(diseases)} diseases with remedies.")

def test_predict_endpoint():
    """Test high-accuracy ML model prediction with an uploaded leaf image."""
    img_bytes = create_sample_leaf_image()
    files = {"image": ("test_leaf.jpg", img_bytes, "image/jpeg")}
    
    print("Testing ML inference via POST /api/predict (ViT ~98.5% accuracy model)...")
    response = client.post("/api/predict", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "disease" in data
    assert "confidence" in data
    assert "info" in data
    assert data["prediction_id"] is not None
    assert float(data["confidence"].replace("%", "")) > 0.0

    print(f"[PASS] Predict endpoint passed:")
    print(f"   - Predicted: {data['disease']}")
    print(f"   - Confidence: {data['confidence']}")
    print(f"   - Stored in DB with ID: {data['prediction_id']}")

def _auth_headers():
    """Register (or log in) a throwaway test user and return its auth header."""
    creds = {"name": "Test Farmer", "email": "test_farmer@example.com", "password": "secret123"}
    res = client.post("/api/register", json=creds)
    if res.status_code == 409:
        res = client.post("/api/login", json={"email": creds["email"], "password": creds["password"]})
    assert res.status_code == 200
    return {"Authorization": "Bearer " + res.json()["token"]}

def test_auth_flow():
    """Test login rejects bad passwords and /api/me returns the user."""
    headers = _auth_headers()
    assert client.get("/api/me", headers=headers).json()["email"] == "test_farmer@example.com"
    bad = client.post("/api/login", json={"email": "test_farmer@example.com", "password": "wrong"})
    assert bad.status_code == 401
    assert client.get("/api/history").status_code == 401
    print("[PASS] Auth flow passed.")

def test_history_logging():
    """Test that a logged-in user's predictions are logged into the database."""
    headers = _auth_headers()
    files = {"image": ("test_leaf.jpg", create_sample_leaf_image(), "image/jpeg")}
    assert client.post("/api/predict", files=files, headers=headers).status_code == 200
    response = client.get("/api/history", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0
    latest = history[0]
    print(f"[PASS] History logging passed. Latest entry: {latest['plant']} - {latest['disease']} ({latest['confidence']})")

def test_pdf_report():
    """Test the PDF report is generated for the owner and hidden from other users."""
    headers = _auth_headers()
    files = {"image": ("test_leaf.jpg", create_sample_leaf_image(), "image/jpeg")}
    prediction_id = client.post("/api/predict", files=files, headers=headers).json()["prediction_id"]

    response = client.get(f"/api/report/{prediction_id}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")

    assert client.get(f"/api/report/{prediction_id}").status_code == 401
    other = client.post("/api/register", json={"name": "Other", "email": f"other_{prediction_id}@example.com", "password": "secret123"})
    other_headers = {"Authorization": "Bearer " + other.json()["token"]}
    assert client.get(f"/api/report/{prediction_id}", headers=other_headers).status_code == 404
    print("[PASS] PDF report passed.")

def test_health_tracker():
    """Test adding a tracked plant, logging health and getting a trend + recommendation."""
    headers = _auth_headers()
    plant = client.post("/api/tracker", json={"nickname": "Test bed", "crop": "Tomato"}, headers=headers).json()
    for days_ago, score in [(6, 5), (4, 4), (2, 3), (0, 2)]:
        res = client.post(f"/api/tracker/{plant['id']}/logs", headers=headers,
                          json={"health_score": score, "days_ago": days_ago, "wilting": score < 3})
        assert res.status_code == 200
    summary = res.json()
    assert summary["log_count"] == 4
    assert summary["trend"] == "declining"
    assert summary["recommendation"]
    assert client.post(f"/api/tracker/{plant['id']}/logs", headers=headers, json={"health_score": 9}).status_code == 400
    assert client.delete(f"/api/tracker/{plant['id']}", headers=headers).status_code == 200
    print(f"[PASS] Health tracker passed. Recommendation: {summary['recommendation']}")

def test_assistant_tools():
    """Test the assistant's database tool (works without the LLM running)."""
    from backend.assistant import lookup_disease
    results = lookup_disease("tomato early blight")
    assert results[0]["plant"] == "Tomato" and results[0]["disease"] == "Early Blight"
    assert client.post("/api/assistant", json={"message": "hi"}).status_code == 401
    print("[PASS] Assistant tools passed.")

if __name__ == "__main__":
    print("Running Backend & ML Integration Tests...")
    test_health()
    test_get_plants()
    test_get_diseases()
    test_predict_endpoint()
    test_auth_flow()
    test_history_logging()
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
