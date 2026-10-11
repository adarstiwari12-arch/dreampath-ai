/* core.js - shared helpers loaded on every page.
   Exposes window.DP = { api, el, toast, formatDuration, formatDate, ring }.
   All dynamic text is inserted with textContent / text nodes, never innerHTML. */
(() => {
  "use strict";
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";

  /** fetch wrapper: JSON in/out, CSRF header, friendly errors, smooth login redirect on 401. */
  async function api(method, url, body) {
    const headers = { Accept: "application/json", "X-CSRF-Token": csrf };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    let res;
    try {
      res = await fetch(url, {
        method, headers, credentials: "same-origin",
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new Error("Network problem. Check your connection and try again.");
    }
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON error page */ }
    if (res.status === 401) {
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.assign(`/login?next=${next}`);
      throw new Error("Please log in to continue.");
    }
    if (!res.ok) {
      const err = new Error((data && data.error) || "Something went wrong. Please try again.");
      err.status = res.status;
      throw err;
    }
    return data;
  }

  /** Tiny DOM builder. Children may be nodes, strings or arrays; null/false are skipped. */
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value === false || value === null || value === undefined) continue;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? "" : value);
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined || child === false) continue;
      node.append(child.nodeType ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  function toast(message, kind = "info") {
    const box = document.getElementById("toasts");
    if (!box) return;
    const t = el("div", { class: "toast" + (kind === "error" ? " is-error" : ""), role: "status", text: message });
    box.append(t);
    setTimeout(() => t.remove(), 4200);
  }

  /** 90 -> "1 h 30 min", 300 -> "5 h", 45 -> "45 min" */
  function formatDuration(minutes) {
    const m = Math.round(minutes);
    const h = Math.floor(m / 60), r = m % 60;
    if (!h) return `${r} min`;
    return r ? `${h} h ${r} min` : `${h} h`;
  }

  /** "2026-11-26" -> "26 Nov 2026" (local calendar date, no timezone shifts) */
  function formatDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  }

  /** Circular meter. Returns { update(percent) }. */
  function ring(container, percent = 0) {
    const NS = "http://www.w3.org/2000/svg";
    const R = 54, C = 2 * Math.PI * R;
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 130 130");
    svg.setAttribute("aria-hidden", "true");
    const circle = (cls) => {
      const c = document.createElementNS(NS, "circle");
      for (const [k, v] of Object.entries({ cx: 65, cy: 65, r: R, fill: "none", "stroke-width": 11, class: cls })) c.setAttribute(k, String(v));
      return c;
    };
    const track = circle("ring-track"), fill = circle("ring-fill");
    fill.setAttribute("stroke-linecap", "round");
    fill.setAttribute("stroke-dasharray", String(C));
    svg.append(track, fill);
    const num = el("span", { class: "ring-num" });
    container.replaceChildren(svg, el("div", { class: "ring-text" }, num, el("span", { class: "ring-sub", text: "Dream Meter" })));
    container.setAttribute("role", "img");
    function update(p) {
      const v = Math.max(0, Math.min(100, p));
      fill.setAttribute("stroke-dashoffset", String(C * (1 - v / 100)));
      num.textContent = `${Math.round(v * 10) / 10}%`;
      container.setAttribute("aria-label", `Dream Meter ${Math.round(v)} percent`);
    }
    update(percent);
    return { update };
  }

  document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".nav-toggle");
    const panel = document.getElementById("header-panel");
    toggle?.addEventListener("click", () => {
      const open = panel.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });

    // Account dropdown
    const menu = document.querySelector("[data-menu]");
    if (menu) {
      const btn = menu.querySelector(".avatar"), pop = menu.querySelector(".menu-panel");
      const close = (refocus) => { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); if (refocus) btn.focus(); };
      btn.addEventListener("click", () => {
        const opening = pop.hidden;
        pop.hidden = !opening;
        btn.setAttribute("aria-expanded", String(opening));
      });
      document.addEventListener("click", (e) => { if (!pop.hidden && !menu.contains(e.target)) close(false); });
      document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape") return;
        if (!pop.hidden) close(true);
        if (panel?.classList.contains("is-open")) { panel.classList.remove("is-open"); toggle?.setAttribute("aria-expanded", "false"); }
      });
    }

    // Loading state on submit buttons (only if the form was not blocked by validation)
    document.querySelectorAll("form").forEach((form) => {
      form.addEventListener("submit", (e) => {
        const btn = form.querySelector("button[type=submit][data-loading-text]");
        if (!btn) return;
        setTimeout(() => {
          if (e.defaultPrevented || !btn.isConnected) return;
          btn.classList.add("is-loading"); btn.disabled = true;
        }, 0);
      });
    });
    window.addEventListener("pageshow", (e) => {
      if (!e.persisted) return;  // back/forward cache: undo the loading state
      document.querySelectorAll("button.is-loading").forEach((b) => { b.classList.remove("is-loading"); b.disabled = false; });
    });

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
      form.addEventListener("submit", (e) => { if (!window.confirm(form.dataset.confirm)) e.preventDefault(); });
    });
    document.querySelectorAll(".flash-success, .flash-info").forEach((n) => setTimeout(() => n.remove(), 7000));
  });

  window.DP = { api, el, toast, formatDuration, formatDate, ring };
})();
