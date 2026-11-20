// ---------- Upload helpers: photo quality check, drag & drop, phone camera ----------
const UploadTools = (function () {
  const MAX_SIDE = 256;          // analyse a small copy, it's fast and good enough
  const BLUR_LIMIT = 40;         // Laplacian variance below this looks blurry
  const DARK_LIMIT = 55;         // average brightness (0-255)
  const BRIGHT_LIMIT = 225;
  const MIN_PIXELS = 200;        // smallest side of the original photo

  function loadImage(file) {
    return new Promise(function (resolve, reject) {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = function () { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error("Could not read the image.")); };
      img.src = url;
    });
  }

  // Returns { sharpness, brightness, warnings[] } for a photo
  function checkQuality(file) {
    return loadImage(file).then(function (img) {
      const scale = Math.min(1, MAX_SIDE / Math.max(img.width, img.height));
      const w = Math.max(3, Math.round(img.width * scale));
      const h = Math.max(3, Math.round(img.height * scale));
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);
      const data = ctx.getImageData(0, 0, w, h).data;

      // Grayscale copy + average brightness
      const gray = new Float32Array(w * h);
      let sum = 0;
      for (let i = 0; i < w * h; i++) {
        const v = 0.299 * data[i * 4] + 0.587 * data[i * 4 + 1] + 0.114 * data[i * 4 + 2];
        gray[i] = v;
        sum += v;
      }
      const brightness = sum / (w * h);

      // Sharpness: variance of the Laplacian (edges are weak in blurry photos)
      let lapSum = 0, lapSq = 0, n = 0;
      for (let y = 1; y < h - 1; y++) {
        for (let x = 1; x < w - 1; x++) {
          const i = y * w + x;
          const lap = gray[i - w] + gray[i + w] + gray[i - 1] + gray[i + 1] - 4 * gray[i];
          lapSum += lap;
          lapSq += lap * lap;
          n++;
        }
      }
      const mean = lapSum / n;
      const sharpness = lapSq / n - mean * mean;

      const warnings = [];
      if (Math.min(img.width, img.height) < MIN_PIXELS) warnings.push("The photo is very small – move closer or use a higher resolution.");
      if (sharpness < BLUR_LIMIT) warnings.push("The photo looks blurry – hold the camera steady and tap to focus on the leaf.");
      if (brightness < DARK_LIMIT) warnings.push("The photo is too dark – take it in daylight or better light.");
      if (brightness > BRIGHT_LIMIT) warnings.push("The photo is too bright – avoid direct glare on the leaf.");
      return { sharpness: Math.round(sharpness), brightness: Math.round(brightness), warnings: warnings };
    });
  }

  // Let a box accept dropped image files
  function enableDrop(el, onFiles) {
    if (!el) return;
    ["dragenter", "dragover"].forEach(function (type) {
      el.addEventListener(type, function (e) {
        e.preventDefault();
        el.classList.add("drag-over");
      });
    });
    ["dragleave", "drop"].forEach(function (type) {
      el.addEventListener(type, function (e) {
        e.preventDefault();
        el.classList.remove("drag-over");
      });
    });
    el.addEventListener("drop", function (e) {
      const files = Array.from(e.dataTransfer.files || []).filter(function (f) { return /^image\//.test(f.type); });
      if (files.length) onFiles(files);
    });
  }

  // Put files into an <input type="file"> and fire its change event (reuses the page's own validation)
  function setInputFiles(input, files) {
    const dt = new DataTransfer();
    files.forEach(function (f) { dt.items.add(f); });
    input.files = dt.files;
    input.dispatchEvent(new Event("change"));
  }

  function isTouchDevice() {
    return window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
  }

  // On phones, add a "Take a photo" button that opens the rear camera directly
  function addCameraButton(afterEl, onFile) {
    if (!afterEl || !isTouchDevice()) return;
    const camInput = document.createElement("input");
    camInput.type = "file";
    camInput.accept = "image/*";
    camInput.setAttribute("capture", "environment");
    camInput.hidden = true;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "plant-select-btn camera-btn";
    btn.textContent = "📷 Take a photo";
    btn.addEventListener("click", function () { camInput.click(); });
    camInput.addEventListener("change", function () {
      if (camInput.files[0]) onFile(camInput.files[0]);
    });
    afterEl.insertAdjacentElement("afterend", btn);
    btn.insertAdjacentElement("afterend", camInput);
  }

  return { checkQuality: checkQuality, enableDrop: enableDrop, setInputFiles: setInputFiles, addCameraButton: addCameraButton };
})();
