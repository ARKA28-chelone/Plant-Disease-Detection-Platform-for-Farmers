import io
import os

if os.getenv("VERCEL"):
    os.environ.setdefault("HF_HOME", "/tmp/huggingface")

from PIL import Image
from transformers import pipeline
from backend.disease_data import get_disease_info

# Meta DINOv2 vision transformer fine-tuned on PlantVillage (~98.5%+ accuracy)
MODEL_ID = "rodynaemad/plant-disease-dinov2-small"

class PlantDiseaseClassifier:
    _instance = None

    def __init__(self):
        print(f"Loading state-of-the-art DINOv2 model: {MODEL_ID} ...")
        self.pipe = pipeline(
            "image-classification",
            model=MODEL_ID,
            top_k=5
        )
        print("DINOv2 model loaded successfully with high precision!")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, image_input, selected_plant: str = None):
        """
        Accepts PIL Image, file path, or bytes, and optional selected_plant.
        Returns high-confidence prediction and remedies.
        """
        if isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, str):
            image = Image.open(image_input).convert("RGB")
        else:
            image = image_input.convert("RGB")

        # Run inference across all 38 classes
        results = self.pipe(image)
        top_result = results[0]

        top_label = top_result["label"]
        top_score_pct = round(float(top_result["score"]) * 100, 2)

        # Parse detected plant from label (e.g. 'Potato___Early_blight' -> 'Potato')
        detected_plant = top_label.split("___")[0].replace("_", " ").strip()

        warning_note = None
        chosen_result = top_result

        # Check if user specified a crop
        has_user_crop = selected_plant and selected_plant.lower() not in ("auto", "all", "", "none")

        if has_user_crop:
            user_crop = selected_plant.strip()
            # If the top prediction belongs to the selected crop, perfect match!
            if user_crop.lower() in detected_plant.lower():
                chosen_result = top_result
            else:
                # The visual analysis detected a different crop
                if top_score_pct >= 40.0:
                    # Visual confidence is high for another crop -> do NOT force wrong crop!
                    chosen_result = top_result
                    warning_note = (
                        f"Notice: You selected '{user_crop}', but our AI model identified this leaf "
                        f"as '{detected_plant}' with high confidence ({top_score_pct}%). "
                        f"The diagnosis and remedies below are for {detected_plant}."
                    )
                else:
                    # Search if user crop exists in top candidates
                    matching = [
                        r for r in results 
                        if user_crop.lower() in r["label"].lower().replace("_", " ")
                    ]
                    if matching:
                        chosen_result = matching[0]

        raw_label = chosen_result["label"]
        confidence_pct = round(float(chosen_result["score"]) * 100, 2)

        # Retrieve knowledge base details
        info = get_disease_info(raw_label)
        plant_name = info["plant"]
        disease_name = info["disease"]

        # Format treatments as clean readable text
        treatments_text = ""
        for t_type, recommendation in info["treatments"]:
            treatments_text += f"\n• [{t_type}] {recommendation}"

        formatted_info = (
            f"Pathogen: {info['pathogen']}\n"
            f"Symptoms: {info['symptoms']}\n"
            f"Prevention: {info['prevention']}\n"
            f"Treatments:{treatments_text}"
        )

        top_candidates = [
            {"label": r["label"], "score": round(float(r["score"]) * 100, 2)}
            for r in results
        ]

        return {
            "raw_label": raw_label,
            "plant": plant_name,
            "disease_name": disease_name,
            "disease": f"{plant_name} - {disease_name}",
            "confidence": f"{confidence_pct}%",
            "confidence_value": confidence_pct,
            "info": formatted_info,
            "details": info,
            "warning_note": warning_note,
            "top_candidates": top_candidates
        }

def get_classifier():
    return PlantDiseaseClassifier.get_instance()
