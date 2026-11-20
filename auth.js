// ---------- Shared login state (used by every page) ----------
// The token from /api/login is kept in localStorage and sent as a Bearer header.
const Auth = (function () {
  const apiBase = (window.location.protocol === "file:") ? "http://127.0.0.1:8000" : "";

  function getToken() {
    try { return localStorage.getItem("pc_token"); } catch (e) { return null; }
  }
  function getUser() {
    try { return JSON.parse(localStorage.getItem("pc_user")); } catch (e) { return null; }
  }
  function save(token, user) {
    localStorage.setItem("pc_token", token);
    localStorage.setItem("pc_user", JSON.stringify(user));
  }
  function saveUser(user) {
    try { localStorage.setItem("pc_user", JSON.stringify(user)); } catch (e) { /* ignore */ }
  }
  function clear() {
    localStorage.removeItem("pc_token");
    localStorage.removeItem("pc_user");
  }
  function logout() {
    clear();
    window.location.href = "index.html";
  }
  function authHeaders() {
    const t = getToken();
    return t ? { Authorization: "Bearer " + t } : {};
  }

  // fetch wrapper: adds the token and turns API errors into readable messages
  function request(path, options) {
    options = options || {};
    options.headers = Object.assign({}, options.headers, authHeaders());
    return fetch(apiBase + path, options).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        // Token expired or invalid: forget it so the UI shows "Login" again
        if (res.status === 401 && getToken() && path !== "/api/login") clear();
        if (!res.ok) throw new Error(data.detail || ("Server returned status " + res.status));
        return data;
      });
    });
  }

  // JSON helper for POST/PATCH/DELETE bodies
  function send(method, path, body) {
    return request(path, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    });
  }

  function escapeHtml(s) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" };
    return String(s).replace(/[&<>"']/g, function (c) { return map[c]; });
  }

  // Dates from the API are UTC without a zone suffix
  function toDate(iso) {
    return iso ? new Date(iso.replace(/(\+00:00|Z)?$/, "Z")) : null;
  }

  // Download a file (PDF/CSV) from an endpoint that needs the auth header
  function download(path, button, fallbackName) {
    const label = button ? button.textContent : "";
    if (button) { button.disabled = true; button.textContent = "Preparing..."; }
    return fetch(apiBase + path, { headers: authHeaders() })
      .then(function (res) {
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (data) {
            throw new Error(data.detail || ("Server returned status " + res.status));
          });
        }
        const match = /filename="([^"]+)"/.exec(res.headers.get("Content-Disposition") || "");
        return res.blob().then(function (blob) {
          const link = document.createElement("a");
          link.href = URL.createObjectURL(blob);
          link.download = match ? match[1] : fallbackName;
          document.body.appendChild(link);
          link.click();
          link.remove();
          setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
        });
      })
      .finally(function () {
        if (button) { button.disabled = false; button.textContent = label; }
      });
  }

  function downloadReport(predictionId, button) {
    return download("/api/report/" + predictionId, button, "PlantCare_Report.pdf");
  }

  // Show "Login" or "Name · Logout" at the end of the navbar (+ Admin for admins)
  function renderNav() {
    const nav = document.querySelector(".navbar nav");
    if (!nav) return;
    const old = nav.querySelector(".nav-auth");
    if (old) old.remove();
    const user = getUser();
    const slot = document.createElement("span");
    slot.className = "nav-auth";
    if (user) {
      slot.innerHTML = (user.is_admin ? '<a href="admin.html">Admin</a>' : "") +
        '<a class="nav-user" href="profile.html" title="My profile">👤 ' + escapeHtml(user.name.split(" ")[0]) + "</a>" +
        '<button type="button" class="nav-btn" id="logoutBtn">Logout</button>';
      slot.querySelector("#logoutBtn").addEventListener("click", logout);
    } else if (!document.body.classList.contains("auth-page")) {
      slot.innerHTML = '<a class="nav-btn" href="login.html">Login</a>';
    }
    nav.appendChild(slot);
    markActiveLink();
  }

  // Underline the navbar link for the page being viewed
  function markActiveLink() {
    const page = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".navbar nav a").forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === page);
    });
  }

  // Refresh the stored user (name / admin flag may have changed since login)
  function refreshUser() {
    if (!getToken()) return;
    request("/api/me").then(function (user) {
      const before = JSON.stringify(getUser());
      saveUser(user);
      if (JSON.stringify(user) !== before) renderNav();
    }).catch(function () {
      if (!getToken()) renderNav();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderNav();
    refreshUser();
  });

  // Installable app + offline page (only works when served over http(s), not file://)
  if ("serviceWorker" in navigator && window.location.protocol.indexOf("http") === 0) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () { /* optional feature */ });
    });
  }

  return {
    apiBase: apiBase, getToken: getToken, getUser: getUser, save: save, saveUser: saveUser, logout: logout,
    authHeaders: authHeaders, request: request, send: send, escapeHtml: escapeHtml, toDate: toDate,
    download: download, downloadReport: downloadReport, renderNav: renderNav
  };
})();
