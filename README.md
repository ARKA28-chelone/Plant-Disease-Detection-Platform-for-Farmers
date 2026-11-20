# 🌿 PlantCare ML – Plant Disease Detection Using Machine Learning

DBMS project: upload a photo of a plant leaf, a machine learning model identifies the disease, and the
system stores scans, health logs and reports in a relational database.

## Quick start

```bash
pip install -r requirements.txt
python run_server.py
```

Open **http://127.0.0.1:8000/** · API docs at **http://127.0.0.1:8000/docs**

- First run downloads the vision model (`rodynaemad/plant-disease-dinov2-small`, from Hugging Face) – needs internet once.
- The farmer assistant needs [Ollama](https://ollama.com) running with the model pulled:
  `ollama pull qwen2.5:3b-instruct`. Without Ollama, the assistant falls back to answering from the disease database.
- Run the tests: `python -m pytest -q` (tests use a temporary database, never `plant_disease.db`).

## Features

| Area | What it does | Page |
|---|---|---|
| Disease detection | Upload a leaf photo, pick a crop (or auto), get disease + confidence + treatment info | Home → Detection |
| Smarter upload | Drag & drop, phone camera button, photo quality check (blurry / dark / bright / too small) | Home, Batch |
| Other possibilities | The model's next best guesses with confidence bars, saved with each scan | Home result, Report |
| Batch scan | Scan up to 10 leaves at once with a summary of the most common problem | `batch.html` |
| Accounts | Sign up / log in (salted PBKDF2 password hashing, signed tokens) | `login.html` |
| PDF health report | One-page report: leaf image, scan details, diagnosis, treatment plan, checklist, notes | Report, Dashboard |
| Dashboard | Stats, model accuracy from user feedback, scans by plant, search & filters, reminders, CSV export | `dashboard.html` |
| Scan report | Full disease info, 👍/👎 feedback, notes, link to a tracked plant, re-scan reminder, ask the assistant | `results.html` |
| Before & after | Compare two scans of a plant with a plain-language verdict (recovered / no improvement / …) | `compare.html` |
| Health tracker | Track plants, log health 1–5 + symptoms, chart over time, trend, recommendation, summary PDF | `tracker.html` |
| Krishi Mitra assistant | Open-source LLM agent (Qwen2.5 via Ollama) that uses tools to read the disease DB, your scans and plants | `assistant.html` + 💬 button on every page |
| Disease library | Every condition the model knows, with search and crop filters | `diseases.html` |
| Profile | Change name / password, export data, delete account (with all data) | `profile.html` |
| Admin | Users, scans per day, most common diseases, model accuracy across all users | `admin.html` |
| Hindi / English | One-click language toggle in the navbar (the assistant understands Hindi, replies in English) | all pages |
| Installable app | Add to phone home screen; offline page when there is no connection | all pages |

### Admin access

```bash
python -m backend.make_admin you@example.com           # give admin
python -m backend.make_admin you@example.com --remove  # take it away
```

### Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite:///./plant_disease.db` | Any SQLAlchemy URL, e.g. MySQL |
| `UPLOAD_DIR` | `uploads` | Where leaf photos are stored |
| `AUTH_SECRET` | dev value | **Set this in production** – signs login tokens |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama server |
| `OLLAMA_MODEL` | `qwen2.5:3b-instruct` | Assistant model (a 7B model, e.g. `qwen2.5:7b-instruct`, gives better answers and Hindi) |

## Database design

| Table | Purpose | Key relationships |
|---|---|---|
| `plants` | Crops (Tomato, Potato, …) | 1 → many `diseases` |
| `diseases` | Disease name, pathogen, symptoms, prevention | many → 1 `plants`, 1 → many `treatments` |
| `treatments` | Organic / chemical / cultural remedies | many → 1 `diseases` |
| `users` | Accounts (hashed passwords, admin flag) | 1 → many `predictions`, `tracked_plants`, `reminders` |
| `predictions` | Every scan: image, label, confidence, notes, top guesses | many → 1 `users`, optional many → 1 `tracked_plants` |
| `prediction_feedback` | User's verdict on a prediction (correct / actual disease) | 1 → 1 `predictions` |
| `tracked_plants` | Plants a farmer monitors | many → 1 `users`, 1 → many `health_logs` |
| `health_logs` | Dated health score + symptom flags + notes | many → 1 `tracked_plants` |
| `reminders` | Re-scan / check-up reminders with due dates | many → 1 `users`, optional link to a scan or plant |

## Project structure

```
backend/
  main.py          FastAPI app: auth, prediction, tracker, assistant, pages
  features.py      History filters, notes, feedback, profile, reminders, CSV export, admin
  models.py        SQLAlchemy tables
  ml_engine.py     DINOv2 leaf classifier
  report.py        PDF reports (scan report + plant summary)
  tracker.py       Health trend + recommendations
  assistant.py     Krishi Mitra tool-using agent (Ollama)
  auth.py          Password hashing + signed tokens
  make_admin.py    Grant / remove admin
*.html             Pages (shared theme in style.css)
auth.js            Login state, navbar, API helpers (every page)
i18n.js            Hindi / English toggle
chat-widget.js     Floating assistant button
upload-tools.js    Photo quality check, drag & drop, camera
sw.js, manifest.json, icons/   Installable app
```
