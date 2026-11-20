from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Plant(Base):
    __tablename__ = "plants"

    plant_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    scientific_name = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)

    diseases = relationship("Disease", back_populates="plant", cascade="all, delete-orphan")


class Disease(Base):
    __tablename__ = "diseases"

    disease_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plants.plant_id"), nullable=False)
    class_name = Column(String(150), unique=True, nullable=False, index=True) # e.g. "Tomato___Early_blight"
    name = Column(String(150), nullable=False)                                # e.g. "Early Blight"
    pathogen_type = Column(String(50), default="Fungal")                      # Fungal, Bacterial, Viral, Healthy
    symptoms = Column(Text, nullable=False)
    prevention = Column(Text, nullable=True)

    plant = relationship("Plant", back_populates="diseases")
    treatments = relationship("Treatment", back_populates="disease", cascade="all, delete-orphan")


class Treatment(Base):
    __tablename__ = "treatments"

    treatment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    disease_id = Column(Integer, ForeignKey("diseases.disease_id"), nullable=False)
    treatment_type = Column(String(50), nullable=False) # "Organic", "Chemical", "Cultural"
    recommendation = Column(Text, nullable=False)

    disease = relationship("Disease", back_populates="treatments")


from datetime import datetime, timezone

class PredictionRecord(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_filename = Column(String(255), nullable=False)
    predicted_label = Column(String(150), nullable=False)
    plant_name = Column(String(100), nullable=False)
    disease_name = Column(String(150), nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String(50), default="SUCCESS")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    tracked_id = Column(Integer, ForeignKey("tracked_plants.tracked_id"), nullable=True)  # optional link to a tracked plant
    notes = Column(Text, nullable=True)                                                    # farmer's own notes on the scan
    candidates = Column(Text, nullable=True)                                               # JSON list of the model's top guesses

    feedback = relationship("PredictionFeedback", uselist=False, cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TrackedPlant(Base):
    __tablename__ = "tracked_plants"

    tracked_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    nickname = Column(String(100), nullable=False)       # e.g. "Back field tomatoes"
    crop = Column(String(100), nullable=False)           # Tomato, Potato, Pepper, Corn, ...
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    logs = relationship("HealthLog", back_populates="plant", cascade="all, delete-orphan",
                        order_by="HealthLog.logged_at")


class HealthLog(Base):
    __tablename__ = "health_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tracked_id = Column(Integer, ForeignKey("tracked_plants.tracked_id"), nullable=False, index=True)
    health_score = Column(Integer, nullable=False)       # 1 (very poor) - 5 (excellent)
    leaf_spots = Column(Integer, default=0)              # 0/1 flags for quick symptom checks
    yellowing = Column(Integer, default=0)
    wilting = Column(Integer, default=0)
    pests = Column(Integer, default=0)
    watered = Column(Integer, default=0)
    treated = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    plant = relationship("TrackedPlant", back_populates="logs")


class PredictionFeedback(Base):
    """Farmer's verdict on whether a prediction was right (used to measure model accuracy)."""
    __tablename__ = "prediction_feedback"

    feedback_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id"), unique=True, nullable=False)
    is_correct = Column(Integer, nullable=False)          # 1 = correct, 0 = wrong
    correct_disease = Column(String(150), nullable=True)  # what the farmer says it really was
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Reminder(Base):
    __tablename__ = "reminders"

    reminder_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id"), nullable=True)
    tracked_id = Column(Integer, ForeignKey("tracked_plants.tracked_id"), nullable=True)
    message = Column(String(255), nullable=False)
    due_at = Column(DateTime, nullable=False)
    done = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
