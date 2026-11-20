from sqlalchemy import inspect, text
from backend.database import engine, Base, SessionLocal
from backend.models import Plant, Disease, Treatment
from backend.disease_data import KNOWLEDGE_BASE

def initialize_database():
    """Create all tables and seed data if not present."""
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Plant).count() > 0:
            print("Database already initialized and seeded.")
            return

        print("Seeding database with plant and disease data...")
        plant_cache = {}

        for class_name, info in KNOWLEDGE_BASE.items():
            plant_name = info["plant"]
            
            # Find or create plant
            if plant_name not in plant_cache:
                plant = db.query(Plant).filter(Plant.name == plant_name).first()
                if not plant:
                    plant = Plant(
                        name=plant_name,
                        scientific_name=f"Solanum / Zea / {plant_name}",
                        description=f"Cultivated {plant_name} crop."
                    )
                    db.add(plant)
                    db.flush()
                plant_cache[plant_name] = plant

            plant_obj = plant_cache[plant_name]

            # Create disease record
            disease = Disease(
                plant_id=plant_obj.plant_id,
                class_name=class_name,
                name=info["disease"],
                pathogen_type=info["pathogen"],
                symptoms=info["symptoms"],
                prevention=info["prevention"]
            )
            db.add(disease)
            db.flush()

            # Create treatments
            for treat_type, recommendation in info["treatments"]:
                treatment = Treatment(
                    disease_id=disease.disease_id,
                    treatment_type=treat_type,
                    recommendation=recommendation
                )
                db.add(treatment)

        db.commit()
        print("Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database()


def _add_missing_columns():
    """create_all() won't alter existing tables, so add newer columns to older databases."""
    wanted = {
        "predictions": [("user_id", "INTEGER REFERENCES users(user_id)"),
                        ("tracked_id", "INTEGER REFERENCES tracked_plants(tracked_id)"),
                        ("notes", "TEXT"),
                        ("candidates", "TEXT")],
        "users": [("is_admin", "INTEGER DEFAULT 0")],
    }
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, columns in wanted.items():
            existing = [c["name"] for c in inspector.get_columns(table)]
            for name, ddl in columns:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
