"""
"Krishi Mitra" farmer assistant: a small tool-using AI agent.

Runs an open-source LLM (Qwen2.5 3B Instruct by default) locally through
Ollama. The model can call tools to look things up in this app's disease
database and in the farmer's own scans and health logs, so its answers are
grounded in real data instead of guesses.
"""
import os
import json
import urllib.request
import urllib.error

from backend.disease_data import KNOWLEDGE_BASE
from backend.models import PredictionRecord, TrackedPlant
from backend.tracker import health_trend

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = (
    "You are Krishi Mitra, a friendly farming assistant inside the PlantCare ML app. "
    "You help farmers with crop diseases, pests, watering, soil and general plant care. "
    "Use the tools to look up diseases in the app's database and to check the farmer's own "
    "scans and plant health logs whenever the question relates to them. "
    "Answer in simple, practical language in at most 6 short sentences or bullet points. "
    "Prefer organic and cultural methods first, and remind the farmer to read pesticide labels "
    "when suggesting chemicals. If you are not sure, say so and suggest scanning a leaf or "
    "contacting a local agricultural extension officer. Politely decline topics unrelated to farming. "
    "Never invent phone numbers, hotlines, websites, brand names or services. When database facts are "
    "provided, base your treatment advice on them."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_disease",
            "description": "Search the PlantCare disease database for symptoms, prevention and treatments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Crop and/or disease name, e.g. 'tomato late blight'"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_recent_scans",
            "description": "Get the farmer's most recent leaf scan results (plant, disease, confidence, date).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_tracked_plants",
            "description": "Get the farmer's tracked plants with their latest health score, trend and symptoms.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ---------- Tools ----------

def lookup_disease(query: str) -> list:
    words = [w for w in query.lower().replace("_", " ").split() if len(w) > 2]
    scored = []
    for key, info in KNOWLEDGE_BASE.items():
        haystack = f"{info['plant']} {info['disease']} {key}".lower().replace("_", " ")
        score = sum(1 for w in words if w in haystack)
        if score:
            scored.append((score, info))
    scored.sort(key=lambda s: -s[0])
    return [
        {
            "plant": info["plant"],
            "disease": info["disease"],
            "pathogen": info.get("pathogen"),
            "symptoms": info.get("symptoms"),
            "prevention": info.get("prevention"),
            "treatments": [f"{kind}: {text}" for kind, text in info.get("treatments", [])],
        }
        for _, info in scored[:3]
    ] or [{"result": "No matching disease found in the database."}]


def _matching_diseases(question: str) -> list:
    """Diseases clearly named in the question (crop + disease words both match)."""
    q = question.lower().replace("_", " ")
    found = []
    for info in KNOWLEDGE_BASE.values():
        disease_words = [w for w in info["disease"].lower().replace("_", " ").split() if len(w) > 3]
        if "healthy" in info["disease"].lower() or not disease_words:
            continue
        if info["plant"].lower() in q and all(w in q for w in disease_words):
            found.append(info)
    return [lookup_disease(f"{i['plant']} {i['disease']}")[0] for i in found[:2]]


def get_my_recent_scans(db, user) -> list:
    records = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.user_id == user.user_id)
        .order_by(PredictionRecord.created_at.desc())
        .limit(5)
        .all()
    )
    return [
        {"plant": r.plant_name, "disease": r.disease_name, "confidence": f"{r.confidence:.1f}%",
         "date": r.created_at.strftime("%d %b %Y") if r.created_at else None}
        for r in records
    ] or [{"result": "The farmer has no scans yet."}]


def get_my_tracked_plants(db, user) -> list:
    plants = db.query(TrackedPlant).filter(TrackedPlant.user_id == user.user_id).all()
    result = []
    for p in plants:
        last = p.logs[-1] if p.logs else None
        symptoms = [s.replace("_", " ") for s in ("leaf_spots", "yellowing", "wilting", "pests")
                    if last and getattr(last, s)]
        result.append({
            "plant": f"{p.nickname} ({p.crop})",
            "latest_health_score_out_of_5": last.health_score if last else None,
            "trend": health_trend(p.logs),
            "latest_symptoms": symptoms or ["none"],
            "latest_notes": last.notes if last else None,
        })
    return result or [{"result": "The farmer is not tracking any plants yet."}]


def _run_tool(name, args, db, user):
    if name == "lookup_disease":
        return lookup_disease(str(args.get("query", "")))
    if name == "get_my_recent_scans":
        return get_my_recent_scans(db, user)
    if name == "get_my_tracked_plants":
        return get_my_tracked_plants(db, user)
    return {"error": f"Unknown tool {name}"}


# ---------- Agent loop ----------

def _ollama_chat(messages, temperature=0.3):
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": TOOLS,
        "stream": False,
        "options": {"temperature": temperature, "repeat_penalty": 1.15},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read())["message"]


def ask(question: str, history: list, db, user, language: str = "en") -> dict:
    """Answer a farmer's question, letting the model call tools as needed."""
    prompt = SYSTEM_PROMPT
    if language == "hi":
        # The local 3B model writes unreliable Hindi, so it understands Hindi/Hinglish but answers in English
        prompt += (" The farmer may write in Hindi or Hinglish. Understand it, but reply in clear, "
                   "simple English that is easy to translate.")
    messages = [{"role": "system", "content": prompt}]
    temperature = 0.3
    # Keep only the last few turns of plain chat history from the browser
    for turn in history[-6:]:
        if turn.get("role") in ("user", "assistant") and isinstance(turn.get("content"), str):
            messages.append({"role": turn["role"], "content": turn["content"][:2000]})
    # Small models don't always call tools, so look up any disease the question names up front
    tools_used = []
    facts = _matching_diseases(question)
    if facts:
        tools_used.append("lookup_disease")
        messages.append({"role": "system", "content": "Database facts for this question: " + json.dumps(facts)})
    messages.append({"role": "user", "content": question})

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            reply = _ollama_chat(messages, temperature)
            calls = reply.get("tool_calls") or []
            if not calls:
                return {"reply": reply.get("content", "").strip(), "tools_used": tools_used, "model": OLLAMA_MODEL}
            messages.append(reply)
            for call in calls:
                fn = call.get("function", {})
                args = fn.get("arguments") or {}
                if isinstance(args, str):
                    args = json.loads(args or "{}")
                tools_used.append(fn.get("name"))
                result = _run_tool(fn.get("name"), args, db, user)
                messages.append({"role": "tool", "content": json.dumps(result)})
        # Out of tool rounds: ask for a final answer without tools
        messages.append({"role": "user", "content": "Please give your final answer now."})
        reply = _ollama_chat(messages, temperature)
        return {"reply": reply.get("content", "").strip(), "tools_used": tools_used, "model": OLLAMA_MODEL}
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return _offline_answer(question)


def _offline_answer(question: str) -> dict:
    """Fallback when Ollama isn't running: answer straight from the disease database."""
    matches = [m for m in lookup_disease(question) if "disease" in m]
    if matches:
        m = matches[0]
        text = (f"{m['plant']} - {m['disease']}\n"
                f"Symptoms: {m['symptoms']}\nPrevention: {m['prevention']}\n"
                "Treatments:\n" + "\n".join("- " + t for t in m["treatments"]))
    else:
        text = ("The AI model is offline right now, and I couldn't find that in the disease database. "
                "Try naming the crop and disease, e.g. 'tomato early blight'.")
    return {"reply": text, "tools_used": ["lookup_disease"], "model": "offline (database lookup)"}
