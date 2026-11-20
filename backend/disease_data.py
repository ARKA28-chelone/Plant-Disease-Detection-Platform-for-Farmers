"""
Knowledge base containing symptom definitions, cause descriptions,
and recommended organic/chemical remedies for plant classes.
"""

KNOWLEDGE_BASE = {
    # Tomato
    "Tomato___Early_blight": {
        "plant": "Tomato",
        "disease": "Early Blight",
        "pathogen": "Fungal (Alternaria solani)",
        "symptoms": "Dark brown to black spots with concentric rings ('target board' appearance) on older leaves. Lower foliage yellows and drops prematurely.",
        "prevention": "Practice crop rotation, space plants for adequate airflow, water at the soil line using drip irrigation, and remove infected lower leaves.",
        "treatments": [
            ("Organic", "Apply copper fungicide or neem oil spray every 7-10 days upon first notice."),
            ("Chemical", "Apply protectant fungicides like chlorothalonil, mancozeb, or azoxystrobin as per label instructions.")
        ]
    },
    "Tomato___Late_blight": {
        "plant": "Tomato",
        "disease": "Late Blight",
        "pathogen": "Oomycete / Water Mold (Phytophthora infestans)",
        "symptoms": "Large, irregular, water-soaked grayish lesions on leaves that rapidly turn dark brown. White fungal-like growth appears on leaf undersides in humid weather.",
        "prevention": "Destroy cull piles, use disease-free certified transplants, avoid wet foliage, and maintain wide plant spacing.",
        "treatments": [
            ("Organic", "Apply fixed copper hydroxide or copper sulfate preventive sprays before heavy rains."),
            ("Chemical", "Apply systemic fungicides containing cyazofamid, fluopicolide, or mandipropamid.")
        ]
    },
    "Tomato___Leaf_Mold": {
        "plant": "Tomato",
        "disease": "Leaf Mold",
        "pathogen": "Fungal (Passalora fulva / Cladosporium fulvum)",
        "symptoms": "Pale green or yellow spots on the upper leaf surface, with dense olive-green to grayish velvety mold on the corresponding lower surface.",
        "prevention": "Increase greenhouse ventilation, reduce humidity below 85%, and avoid wetting leaves when watering.",
        "treatments": [
            ("Organic", "Spray with biological control agents like Bacillus subtilis or copper-based fungicides."),
            ("Chemical", "Apply fungicides such as difenoconazole or chlorothalonil.")
        ]
    },
    "Tomato___Bacterial_spot": {
        "plant": "Tomato",
        "disease": "Bacterial Spot",
        "pathogen": "Bacterial (Xanthomonas spp.)",
        "symptoms": "Small (less than 3mm), water-soaked circular dark brown spots on leaves, often surrounded by a yellow halo.",
        "prevention": "Use certified pathogen-free seed, sanitize stakes and tools, and avoid working in wet fields.",
        "treatments": [
            ("Organic", "Apply copper bactericides combined with mancozeb for improved bacterial control."),
            ("Chemical", "Apply fixed copper sprays regularly during early growth stages.")
        ]
    },
    "Tomato___Septoria_leaf_spot": {
        "plant": "Tomato",
        "disease": "Septoria Leaf Spot",
        "pathogen": "Fungal (Septoria lycopersici)",
        "symptoms": "Numerous small circular spots with dark brown margins and gray or tan centers containing tiny black speck pycnidia.",
        "prevention": "Mulch around plants to prevent soil splashing onto lower leaves, rotate crops for 2 years.",
        "treatments": [
            ("Organic", "Remove affected lower leaves immediately; spray with liquid copper."),
            ("Chemical", "Apply chlorothalonil or copper ammonium carbonate.")
        ]
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "plant": "Tomato",
        "disease": "Two-Spotted Spider Mites",
        "pathogen": "Pest (Tetranychus urticae)",
        "symptoms": "Fine yellow or white stippling (speckling) across leaf surfaces, accompanied by delicate silk webbing under leaves.",
        "prevention": "Maintain adequate irrigation to avoid dry/dusty stress conditions; preserve natural predators like ladybugs.",
        "treatments": [
            ("Organic", "Spray insecticidal soap, neem oil, or horticultural oils directly on leaf undersides."),
            ("Chemical", "Apply selective miticides such as abamectin or bifenazate.")
        ]
    },
    "Tomato___Target_Spot": {
        "plant": "Tomato",
        "disease": "Target Spot",
        "pathogen": "Fungal (Corynespora cassiicola)",
        "symptoms": "Small brown spots with light brown centers and dark margins that enlarge into concentric rings.",
        "prevention": "Prune excess suckers to improve airflow; avoid overhead irrigation.",
        "treatments": [
            ("Organic", "Apply copper soaps or biofungicides containing Bacillus amyloliquefaciens."),
            ("Chemical", "Apply boscalid or pyraclostrobin fungicides.")
        ]
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "plant": "Tomato",
        "disease": "Tomato Yellow Leaf Curl Virus (TYLCV)",
        "pathogen": "Viral (Begomovirus transmitted by Whiteflies)",
        "symptoms": "Severe stunting of plants, upward curling and cupping of leaves, mottled yellowing of leaf margins.",
        "prevention": "Use insect-proof netting, yellow sticky traps, and plant TYLCV-resistant varieties.",
        "treatments": [
            ("Organic", "Control whitefly populations using neem oil or reflective silver mulch."),
            ("Chemical", "Apply systemic insecticides like imidacloprid or acetamiprid to manage whitefly vectors.")
        ]
    },
    "Tomato___Tomato_mosaic_virus": {
        "plant": "Tomato",
        "disease": "Tomato Mosaic Virus (ToMV)",
        "pathogen": "Viral (Tobamovirus)",
        "symptoms": "Mottled light and dark green patterns on leaves, distortion, blistering, and fern-like leaf deformation.",
        "prevention": "Wash hands with soap and water after handling tobacco; disinfect pruning shears regularly.",
        "treatments": [
            ("Organic", "Remove and burn or discard infected plants immediately; no chemical cure exists for viruses."),
            ("Cultural", "Grow certified virus-resistant hybrids (labeled Tm-2a).")
        ]
    },
    "Tomato___healthy": {
        "plant": "Tomato",
        "disease": "Healthy Plant",
        "pathogen": "None",
        "symptoms": "Vibrant green leaves, uniform color, and robust foliage with no signs of lesions, wilting, or pests.",
        "prevention": "Continue standard watering schedule, balanced N-P-K fertilization, and periodic monitoring.",
        "treatments": [
            ("Cultural", "Maintain consistent moisture and apply organic compost around root zone.")
        ]
    },

    # Potato
    "Potato___Early_blight": {
        "plant": "Potato",
        "disease": "Early Blight",
        "pathogen": "Fungal (Alternaria solani)",
        "symptoms": "Dark, dry, papery brown spots with concentric ring pattern on older lower leaves. Leaves eventually turn yellow and drop.",
        "prevention": "Plant certified seed tubers, provide adequate nitrogen nutrition, and practice 3-year crop rotation.",
        "treatments": [
            ("Organic", "Apply copper hydroxide or potassium bicarbonate at first symptom."),
            ("Chemical", "Spray protective fungicides such as mancozeb or chlorothalonil.")
        ]
    },
    "Potato___Late_blight": {
        "plant": "Potato",
        "disease": "Late Blight",
        "pathogen": "Oomycete (Phytophthora infestans)",
        "symptoms": "Dark brown to purplish-black water-soaked lesions that spread rapidly across leaves. White spore fuzz on undersides during wet weather.",
        "prevention": "Destroy volunteer potatoes, ensure good hill coverage to protect tubers, avoid sprinkler irrigation late in the day.",
        "treatments": [
            ("Organic", "Apply copper fungicides before rainfall when cool, moist weather is predicted."),
            ("Chemical", "Spray fungicides such as cymoxanil, metalaxyl-M, or dimethomorph.")
        ]
    },
    "Potato___healthy": {
        "plant": "Potato",
        "disease": "Healthy Plant",
        "pathogen": "None",
        "symptoms": "Healthy dark-green potato leaves with crisp texture and uniform growth.",
        "prevention": "Continue standard hilling, balanced fertilization, and pest scouting.",
        "treatments": [
            ("Cultural", "Ensure consistent soil moisture to prevent tuber hollow-heart.")
        ]
    },

    # Pepper (Bell)
    "Pepper,_bell___Bacterial_spot": {
        "plant": "Pepper",
        "disease": "Bacterial Spot",
        "pathogen": "Bacterial (Xanthomonas euvesicatoria)",
        "symptoms": "Small, water-soaked, yellowish-green spots on leaves that turn dark brown with raised centers and yellow halos.",
        "prevention": "Use disease-tested seeds, avoid overhead watering, and avoid entering pepper beds when foliage is wet.",
        "treatments": [
            ("Organic", "Apply copper-based sprays early in the season."),
            ("Chemical", "Tank-mix copper bactericide with mancozeb for enhanced effectiveness.")
        ]
    },
    "Pepper,_bell___healthy": {
        "plant": "Pepper",
        "disease": "Healthy Plant",
        "pathogen": "None",
        "symptoms": "Glossy green leaves, strong erect stems, and no necrotic spots or discolorations.",
        "prevention": "Keep soil well-drained and provide full sun and moderate moisture.",
        "treatments": [
            ("Cultural", "Add calcium-rich amendments to prevent blossom-end rot.")
        ]
    },

    # Corn (Maize)
    "Corn_(maize)___Common_rust_": {
        "plant": "Corn",
        "disease": "Common Rust",
        "pathogen": "Fungal (Puccinia sorghi)",
        "symptoms": "Oval to elongate cinnamon-brown powdery pustules on both upper and lower leaf surfaces.",
        "prevention": "Select resistant corn hybrids; early planting helps avoid high spore concentrations.",
        "treatments": [
            ("Organic", "Apply sulfur-based dust or sulfur sprays early before pustules multiply."),
            ("Chemical", "Apply strobilurin or triazole fungicides if rust reaches upper canopy before tasseling.")
        ]
    },
    "Corn_(maize)___Northern_Leaf_Blight": {
        "plant": "Corn",
        "disease": "Northern Leaf Blight",
        "pathogen": "Fungal (Exserohilum turcicum)",
        "symptoms": "Long, elliptical cigar-shaped grayish-green to tan lesions (1-6 inches long) that parallel leaf margins.",
        "prevention": "Rotate with non-host crops like soybeans; till previous crop residue into the soil.",
        "treatments": [
            ("Organic", "Utilize biofungicides like Trichoderma harzianum soil treatments."),
            ("Chemical", "Apply azoxystrobin or propiconazole fungicides if lesions appear early in the season.")
        ]
    },
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "plant": "Corn",
        "disease": "Gray Leaf Spot",
        "pathogen": "Fungal (Cercospora zeae-maydis)",
        "symptoms": "Small, rectangular, tan-to-gray lesions strictly delimited by the leaf veins, creating a blocky pattern.",
        "prevention": "Plant resistant hybrids; perform crop rotation away from corn for at least 1-2 years.",
        "treatments": [
            ("Organic", "Ensure crop residue management and balanced potassium nutrition."),
            ("Chemical", "Apply pyraclostrobin or fluxapyroxad at silking stage.")
        ]
    },
    "Corn_(maize)___healthy": {
        "plant": "Corn",
        "disease": "Healthy Plant",
        "pathogen": "None",
        "symptoms": "Broad, arching vibrant green leaves with no pustules, streaks, or lesions.",
        "prevention": "Maintain adequate soil nitrogen and weed management.",
        "treatments": [
            ("Cultural", "Ensure consistent water during the critical silking and tassel period.")
        ]
    },

    # Apple
    "Apple___Apple_scab": {
        "plant": "Apple",
        "disease": "Apple Scab",
        "pathogen": "Fungal (Venturia inaequalis)",
        "symptoms": "Dull olive-green to black velvety spots on leaves and fruit, causing leaf distortion and premature leaf drop.",
        "prevention": "Rake and destroy fallen leaves in autumn; prune trees for open sunlight penetration.",
        "treatments": [
            ("Organic", "Apply sulfur or lime-sulfur sprays during green-tip and pink stages."),
            ("Chemical", "Apply captan or myclobutanil fungicides.")
        ]
    },
    "Apple___Black_rot": {
        "plant": "Apple",
        "disease": "Black Rot",
        "pathogen": "Fungal (Botryosphaeria obtusa)",
        "symptoms": "Frogeye leaf spots with purple borders and tan centers; infected fruit develops firm, concentric dark rings.",
        "prevention": "Prune out dead wood, remove mummified fruit, and cut out infected branches.",
        "treatments": [
            ("Organic", "Apply liquid copper sprays during dormant season."),
            ("Chemical", "Apply thiophanate-methyl or captan sprays from petal fall through harvest.")
        ]
    },
    "Apple___Cedar_apple_rust": {
        "plant": "Apple",
        "disease": "Cedar Apple Rust",
        "pathogen": "Fungal (Gymnosporangium juniperi-virginianae)",
        "symptoms": "Bright yellow-orange spots on upper leaf surfaces that develop tiny tube-like structures on the underside.",
        "prevention": "Remove nearby eastern red cedar trees if feasible; choose resistant cultivars.",
        "treatments": [
            ("Organic", "Apply sulfur spray beginning when apple buds open until petals fall."),
            ("Chemical", "Apply myclobutanil or mancozeb at pink bud stage.")
        ]
    },
    "Apple___healthy": {
        "plant": "Apple",
        "disease": "Healthy Plant",
        "pathogen": "None",
        "symptoms": "Lush green foliage with no scab lesions, discoloration, or rust spots.",
        "prevention": "Routine annual pruning and seasonal fertilization.",
        "treatments": [
            ("Cultural", "Monitor orchard seasonally.")
        ]
    },

    # Grape
    "Grape___Black_rot": {
        "plant": "Grape",
        "disease": "Black Rot",
        "pathogen": "Fungal (Guignardia bidwellii)",
        "symptoms": "Small reddish-brown circular leaf spots with black fruiting specks; berries shrivel into hard black mummies.",
        "prevention": "Remove all mummified berries from vines during winter pruning; ensure canopy is well aerated.",
        "treatments": [
            ("Organic", "Apply Bordeaux mixture or copper soap sprays early in the season."),
            ("Chemical", "Apply myclobutanil or tebuconazole fungicides.")
        ]
    },
    "Grape___Esca_(Black_Measles)": {
        "plant": "Grape",
        "disease": "Esca (Black Measles)",
        "pathogen": "Fungal Complex",
        "symptoms": "Tiger-stripe patterns of yellow/red interveinal necrosis on leaves; speckled dark spots on berries.",
        "prevention": "Avoid making large pruning wounds in wet weather; paint pruning wounds with sealant.",
        "treatments": [
            ("Organic", "Apply Trichoderma-based bio-protectants to pruning cuts."),
            ("Chemical", "Remedial surgery to excise diseased wood or vine replacement.")
        ]
    },
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "plant": "Grape",
        "disease": "Leaf Blight (Isariopsis)",
        "pathogen": "Fungal (Phaeoisariopsis vitis)",
        "symptoms": "Irregular dark brown patches that merge and cause premature defoliation of the canopy.",
        "prevention": "Clean fallen leaves; prune for maximum canopy ventilation.",
        "treatments": [
            ("Organic", "Apply copper oxychloride sprays post-harvest."),
            ("Chemical", "Apply broad-spectrum protectant fungicides.")
        ]
    },
    "Grape___healthy": {
        "plant": "Grape",
        "disease": "Healthy Plant",
        "pathogen": "None",
        "symptoms": "Vigorous green grape leaves with clean veins and strong tendril growth.",
        "prevention": "Regular trellising and balanced vine canopy management.",
        "treatments": [
            ("Cultural", "Ensure well-drained soil and adequate sun.")
        ]
    }
}

# Fallback generic helper for any other class in the 38 classes
def get_disease_info(class_name: str):
    if class_name in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[class_name]
    
    # Auto-format for any remaining plant class
    parts = class_name.split("___")
    plant = parts[0].replace("_", " ").strip()
    disease_raw = parts[1].replace("_", " ").strip() if len(parts) > 1 else "Unknown"
    is_healthy = "healthy" in disease_raw.lower()

    if is_healthy:
        return {
            "plant": plant,
            "disease": "Healthy Plant",
            "pathogen": "None",
            "symptoms": f"No signs of disease observed on the {plant} leaf.",
            "prevention": "Maintain optimal irrigation, soil nutrients, and regular crop inspection.",
            "treatments": [
                ("Cultural", f"Continue standard cultural management for {plant}.")
            ]
        }
    else:
        return {
            "plant": plant,
            "disease": disease_raw,
            "pathogen": "Fungal / Microbial Pathogen",
            "symptoms": f"Characteristic spotting, lesions, or foliage discoloration observed on {plant}.",
            "prevention": "Ensure good ventilation, crop rotation, and avoid prolonged leaf wetness.",
            "treatments": [
                ("Organic", "Isolate infected plants and apply organic copper or neem spray."),
                ("Chemical", "Consult local agricultural extension for recommended broad-spectrum fungicide/bactericide.")
            ]
        }
