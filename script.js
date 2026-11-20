// ---------- 1. Plant data ----------
// Static example data for the cards. In the final project this should
// come from a backend API that reads the MySQL database.
const plants = [
  { name: "Tomato", diseases: ["Early Blight", "Late Blight", "Leaf Mold"] },
  { name: "Potato", diseases: ["Early Blight", "Late Blight"] },
  { name: "Pepper", diseases: ["Bacterial Spot"] },
  { name: "Corn",   diseases: ["Common Rust", "Northern Leaf Blight", "Gray Leaf Spot"] }
];

const cardContainer = document.getElementById("plantCards");

// Build one card per plant
if (cardContainer) {
  plants.forEach(function (plant) {
    const items = plant.diseases.map(function (d) {
      return "<li>" + d + "</li>";
    }).join("");

    cardContainer.innerHTML +=
      '<div class="card plant-card-clickable" style="cursor: pointer;" data-plant="' + plant.name + '" title="Click to select ' + plant.name + '"><h3>' + plant.name + "</h3><ul>" + items + "</ul><span style='font-size:0.8rem;color:var(--green);font-weight:600;'>Select " + plant.name + " →</span></div>";
  });

  // Clicking a plant card automatically selects it and scrolls to detection
  cardContainer.querySelectorAll(".plant-card-clickable").forEach(function (card) {
    card.addEventListener("click", function () {
      const pName = card.getAttribute("data-plant");
      selectPlantByName(pName);
      const detectionSec = document.getElementById("detection");
      if (detectionSec) {
        detectionSec.scrollIntoView({ behavior: "smooth" });
      }
    });
  });
}

// ---------- Plant Selection State ----------
let selectedPlant = "auto";

function selectPlantByName(pName) {
  selectedPlant = pName;
  const plantButtons = document.querySelectorAll("#plantSelector .plant-select-btn");
  plantButtons.forEach(function (btn) {
    if (btn.getAttribute("data-plant") === pName) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  const resNote = document.getElementById("resNote");
  if (resNote) {
    if (pName !== "auto") {
      resNote.textContent = "Selected crop: " + pName + ". Please upload a " + pName + " leaf image.";
    } else {
      resNote.textContent = "Auto-detect mode active. Crop type will be identified automatically.";
    }
  }
}

// Bind button clicks in plantSelector
document.querySelectorAll("#plantSelector .plant-select-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const pName = btn.getAttribute("data-plant");
    selectPlantByName(pName);
  });
});

// ---------- 2. Image upload and validation ----------
const imageInput = document.getElementById("imageInput") || document.getElementById("leafImage");
const preview = document.getElementById("preview");
const previewText = document.getElementById("previewText") || document.getElementById("uploadMessage");
const errorMsg = document.getElementById("errorMsg") || document.getElementById("uploadMessage");
const detectBtn = document.getElementById("detectBtn") || document.getElementById("detectButton");

const allowedTypes = ["image/jpeg", "image/png"];
const maxSizeMB = 5;

let selectedFile = null; // holds the valid file, if any

if (imageInput) {
  imageInput.addEventListener("change", function () {
  const file = imageInput.files[0];
  resetImage();

  if (!file) return; // user cancelled

  // Validation: file type
  if (!allowedTypes.includes(file.type)) {
    errorMsg.textContent = "Invalid file type. Please upload a JPG or PNG image.";
    imageInput.value = "";
    return;
  }

  // Validation: file size
  if (file.size > maxSizeMB * 1024 * 1024) {
    errorMsg.textContent = "File is too large. Maximum size is " + maxSizeMB + " MB.";
    imageInput.value = "";
    return;
  }

  // File is valid: store it and show a preview
  selectedFile = file;
  preview.src = URL.createObjectURL(file); // temporary local URL, nothing is uploaded
  preview.hidden = false;
  previewText.hidden = true;
  if (detectBtn) detectBtn.disabled = false;
  });
}

// Clear preview, error and stored file
function resetImage() {
  selectedFile = null;
  if (errorMsg) errorMsg.textContent = "";
  if (preview) {
    preview.hidden = true;
    preview.removeAttribute("src");
  }
  if (previewText) previewText.hidden = false;
  if (detectBtn) detectBtn.disabled = true;
}

// ---------- 3. Detect button ----------
if (detectBtn) {
  detectBtn.addEventListener("click", function () {
  if (!selectedFile) return;

  const apiBase = (window.location.protocol === "file:") ? "http://127.0.0.1:8000" : "";
  const formData = new FormData();
  formData.append("image", selectedFile);
  formData.append("selected_plant", selectedPlant);
  const trackedSelect = document.getElementById("trackedSelect");
  if (trackedSelect && trackedSelect.value) formData.append("tracked_id", trackedSelect.value);

  detectBtn.disabled = true;
  const originalText = detectBtn.textContent;
  detectBtn.textContent = "Analyzing leaf...";
  document.getElementById("resNote").textContent = "Running ML model and querying database...";

  fetch(apiBase + "/api/predict", {
    method: "POST",
    headers: Auth.authHeaders(),
    body: formData
  })
    .then(function (res) {
      if (!res.ok) {
        throw new Error("Server returned status " + res.status);
      }
      return res.json();
    })
    .then(function (data) {
      showResult(data);
      loadHistory();
      const resNote = document.getElementById("resNote");
      if (resNote) {
        if (data.warning_note) {
          resNote.textContent = data.warning_note;
          resNote.style.color = "#c2410c"; // High-visibility warning
        } else {
          resNote.textContent = "Prediction completed with high confidence using DINOv2 vision model.";
          resNote.style.color = "var(--green-dark)";
        }
      }
    })
    .catch(function (err) {
      document.getElementById("resNote").textContent =
        "Error connecting to backend: " + err.message + ". Please ensure the backend server is running.";
    })
    .finally(function () {
      detectBtn.disabled = false;
      detectBtn.textContent = originalText;
    });
  });
}

// Fill the result panel with the backend's prediction
function showResult(data) {
  window.__lastResult = data;
  const elDisease = document.getElementById("resDisease");
  const elConfidence = document.getElementById("resConfidence");
  const elInfo = document.getElementById("resInfo");
  const elBar = document.getElementById("resConfidenceBar");
  const elImage = document.getElementById("resImage");
  const elBadge = document.getElementById("resBadge");

  if (elDisease) elDisease.textContent = data.disease;
  if (elConfidence) elConfidence.textContent = data.confidence;
  if (elInfo) elInfo.textContent = data.info;
  if (elBar) elBar.style.width = parseFloat(data.confidence) + "%";
  if (elImage && data.image_url) {
    elImage.src = data.image_url;
    elImage.hidden = false;
  }
  if (elBadge) {
    const healthy = /healthy/i.test(data.disease);
    elBadge.textContent = healthy ? "Healthy leaf" : "Disease detected";
    elBadge.classList.toggle("ok", healthy);
  }
  showReportButton(data.prediction_id);
  showAlternatives(data.alternatives || []);
}

// The model's other top guesses (the first one is the main result)
function showAlternatives(alts) {
  const box = document.getElementById("altBox");
  if (!box) return;
  const others = alts.slice(1).filter(function (a) { return a.score >= 1; });
  box.hidden = !others.length;
  document.getElementById("altList").innerHTML = others.map(function (a) {
    return '<div class="bar-row wide"><span>' + Auth.escapeHtml(a.plant + " – " + a.disease) + "</span>" +
      '<div class="confidence-bar"><span style="width:' + a.score + '%"></span></div>' +
      "<strong>" + a.score.toFixed(1) + "%</strong></div>";
  }).join("");
}

// ---------- PDF report button ----------
let lastPredictionId = null;
let lastResult = null;

function showReportButton(predictionId) {
  const cta = document.getElementById("reportCta");
  const btn = document.getElementById("downloadReportBtn");
  const hint = document.getElementById("reportHint");
  if (!cta || !btn) return;
  lastPredictionId = predictionId;
  lastResult = window.__lastResult;
  showFeedback(predictionId);
  cta.hidden = false;
  if (Auth.getToken() && predictionId) {
    btn.textContent = "Download PDF Report";
    hint.textContent = "Includes image, diagnosis and treatment plan.";
  } else {
    // Guest scans are not linked to an account, so the report needs a login
    btn.textContent = "Log in to get the PDF Report";
    hint.textContent = "Reports are saved to your account.";
  }
}

const downloadReportBtn = document.getElementById("downloadReportBtn");
if (downloadReportBtn) {
  downloadReportBtn.addEventListener("click", function () {
    if (!Auth.getToken() || !lastPredictionId) {
      window.location.href = "login.html";
      return;
    }
    Auth.downloadReport(lastPredictionId, downloadReportBtn).catch(function (err) {
      document.getElementById("reportHint").textContent = "Could not create report: " + err.message;
    });
  });
}

// ---------- 4. Scan history (logged-in users only) ----------
const historyList = document.getElementById("historyList");

function loadHistory() {
  if (!historyList) return;
  if (!Auth.getToken()) {
    historyList.innerHTML = '<p class="empty-state"><a href="login.html">Log in</a> or ' +
      '<a href="login.html?mode=register">create an account</a> to save and view your scan history.</p>';
    return;
  }
  Auth.request("/api/history?limit=12")
    .then(function (records) {
      if (!records.length) {
        historyList.innerHTML = '<p class="empty-state">No scans yet. <a href="#detection">Analyse your first leaf →</a></p>';
        return;
      }
      historyList.innerHTML = records.map(function (r) {
        // Timestamps are stored in UTC without a zone suffix
        const when = r.created_at ? new Date(r.created_at.replace(/(\+00:00)?$/, "Z")).toLocaleString() : "";
        return '<div class="history-card"><img src="' + r.image_url + '" alt="Leaf scan" loading="lazy">' +
          "<div><strong>" + Auth.escapeHtml(r.disease) + "</strong>" +
          Auth.escapeHtml(r.plant) + " · " + Auth.escapeHtml(r.confidence) +
          "<br><small>" + when + "</small>" +
          '<button type="button" class="pdf-link" data-id="' + r.id + '">📄 PDF Report</button></div></div>';
      }).join("");
    })
    .catch(function (err) {
      if (!Auth.getToken()) return loadHistory(); // token expired: show login prompt
      historyList.innerHTML = '<p class="empty-state">Could not load history: ' + Auth.escapeHtml(err.message) + "</p>";
    });
}

loadHistory();

// One click handler for every "PDF Report" button in the history grid
if (historyList) {
  historyList.addEventListener("click", function (e) {
    const btn = e.target.closest(".pdf-link");
    if (!btn) return;
    e.preventDefault();
    Auth.downloadReport(btn.dataset.id, btn).catch(function (err) { btn.textContent = err.message; });
  });
}

// ---------- Feedback on the prediction (logged-in users) ----------
function showFeedback(predictionId) {
  const row = document.getElementById("feedbackRow");
  const note = document.getElementById("feedbackNote");
  if (!row) return;
  note.textContent = "";
  row.querySelectorAll("button").forEach(function (b) { b.classList.remove("active"); b.disabled = false; });
  row.hidden = !(Auth.getToken() && predictionId);
  if (wrongBox) wrongBox.hidden = true;
}

const feedbackRow = document.getElementById("feedbackRow");
const wrongBox = document.getElementById("wrongBox");

function sendFeedback(isCorrect, correctDisease) {
  const note = document.getElementById("feedbackNote");
  return Auth.send("POST", "/api/scans/" + lastPredictionId + "/feedback",
    { is_correct: isCorrect, correct_disease: correctDisease || null })
    .then(function () {
      feedbackRow.querySelectorAll("button").forEach(function (b) {
        b.classList.toggle("active", b.dataset.feedback === (isCorrect ? "yes" : "no"));
      });
      wrongBox.hidden = true;
      note.textContent = "Thanks for your feedback!";
    })
    .catch(function (err) { note.textContent = "Could not save feedback: " + err.message; });
}

if (feedbackRow) {
  feedbackRow.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-feedback]");
    if (!btn || !lastPredictionId) return;
    if (btn.dataset.feedback === "yes") {
      sendFeedback(true);
      return;
    }
    // Wrong prediction: save right away, then let the farmer say what it really was
    sendFeedback(false).then(function () {
      wrongBox.hidden = false;
      document.getElementById("correctDisease").focus();
      const list = document.getElementById("diseaseOptions");
      if (!list.children.length) {
        Auth.request("/api/diseases").then(function (diseases) {
          list.innerHTML = diseases.map(function (d) {
            return '<option value="' + Auth.escapeHtml(d.plant + " - " + d.name) + '">';
          }).join("");
        });
      }
    });
  });
  wrongBox.addEventListener("submit", function (e) {
    e.preventDefault();
    sendFeedback(false, document.getElementById("correctDisease").value.trim());
  });
}

// ---------- Ask the assistant about this result ----------
const askAssistantBtn = document.getElementById("askAssistantBtn");
if (askAssistantBtn) {
  askAssistantBtn.addEventListener("click", function () {
    const r = lastResult || window.__lastResult;
    if (!r) return;
    const question = /healthy/i.test(r.disease)
      ? "My " + r.plant + " leaf was scanned as healthy (" + r.confidence + "). How do I keep it that way?"
      : "My " + r.plant + " has " + r.disease.replace(r.plant + " - ", "") + " (" + r.confidence + " confidence). What should I do first?";
    if (window.KrishiChat) window.KrishiChat.ask(question);
  });
}

// ---------- Tracked plant dropdown for the detection step ----------
(function loadTrackedPlants() {
  const step = document.getElementById("trackedStep");
  const select = document.getElementById("trackedSelect");
  if (!step || !Auth.getToken()) return;
  Auth.request("/api/tracker").then(function (plants) {
    if (!plants.length) return;
    plants.forEach(function (p) {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.nickname + " (" + p.crop + ")";
      select.appendChild(opt);
    });
    // Coming from the tracker with ?track=<id> preselects that plant
    const wanted = new URLSearchParams(window.location.search).get("track");
    if (wanted) select.value = wanted;
    step.hidden = false;
  }).catch(function () { /* tracker is optional here */ });
})();


// ---------- Smarter upload: drag & drop, phone camera, photo quality check ----------
(function () {
  if (!imageInput || typeof UploadTools === "undefined") return;
  const previewBox = document.querySelector(".preview-box");

  // Quality note sits right under the preview
  const qualityNote = document.createElement("p");
  qualityNote.className = "quality-note";
  qualityNote.hidden = true;
  if (previewBox) previewBox.insertAdjacentElement("afterend", qualityNote);

  // Runs after the page's own type/size validation
  imageInput.addEventListener("change", function () {
    qualityNote.hidden = true;
    if (!selectedFile) return;
    UploadTools.checkQuality(selectedFile).then(function (q) {
      if (!q.warnings.length) return;
      qualityNote.innerHTML = "⚠️ " + q.warnings.map(Auth.escapeHtml).join("<br>⚠️ ") +
        "<br><small>You can still detect, but a clearer photo gives a more reliable result.</small>";
      qualityNote.hidden = false;
    }).catch(function () { /* quality check is only advice */ });
  });

  UploadTools.enableDrop(previewBox, function (files) { UploadTools.setInputFiles(imageInput, [files[0]]); });
  UploadTools.addCameraButton(imageInput, function (file) { UploadTools.setInputFiles(imageInput, [file]); });
  if (previewText && previewText.textContent === "No image selected") {
    previewText.textContent = "No image selected – drop a leaf photo here";
  }
})();
