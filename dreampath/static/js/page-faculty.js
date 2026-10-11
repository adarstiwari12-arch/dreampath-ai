/* page-faculty.js - faculty console: verify, add, edit and delete roadmap lessons. */
document.addEventListener("DOMContentLoaded", async () => {
  const root = document.querySelector("[data-faculty]");
  if (!root) return;
  const { api, el, toast } = window.DP;
  const tabs = root.querySelector("[data-tabs]");
  const rows = root.querySelector("[data-rows]");
  const overview = root.querySelector("[data-overview]");
  const dialog = root.querySelector("[data-dialog]");
  const form = root.querySelector("[data-form]");
  const errBox = root.querySelector("[data-error]");
  const TIERS = ["Starter", "Growth", "Pro", "Elite"];
  let streams = [], current = null, editing = null;

  async function loadOverview() {
    const o = await api("GET", "/api/faculty/overview");
    streams = o.streams;
    overview.replaceChildren(...streams.map((s) => el("div", { class: "card" },
      el("strong", { text: String(s.students) }), el("span", { class: "muted small", text: `${s.name.split(" ")[0]} students` }),
      el("span", { class: "muted small", text: `${s.verified}/${s.steps} verified` }))));
    tabs.replaceChildren(...streams.map((s) => {
      const t = el("button", { type: "button", class: "tab", "aria-pressed": String(s.slug === current), text: s.name });
      t.addEventListener("click", () => { current = s.slug; paintTabs(); loadSteps(); });
      return t;
    }));
  }

  function paintTabs() {
    [...tabs.children].forEach((t, i) => t.setAttribute("aria-pressed", String(streams[i].slug === current)));
  }

  async function loadSteps() {
    const r = await api("GET", `/api/faculty/steps?stream=${encodeURIComponent(current)}`);
    rows.replaceChildren(...r.steps.map(row));
  }

  function row(s) {
    const verify = el("button", { class: "btn btn-ghost btn-sm", type: "button", text: s.verified ? "Unverify" : "Verify" });
    verify.addEventListener("click", () => save(s.id, { ...s, verified: !s.verified }, false));
    const edit = el("button", { class: "btn btn-ghost btn-sm", type: "button", text: "Edit" });
    edit.addEventListener("click", () => openDialog(s));
    const del = el("button", { class: "btn btn-danger-ghost btn-sm", type: "button", text: "Delete" });
    del.addEventListener("click", async () => {
      if (!window.confirm(`Delete "${s.title}"? Students' ticks for it are removed too.`)) return;
      try { await api("DELETE", `/api/faculty/steps/${s.id}`); toast("Lesson deleted."); loadSteps(); loadOverview(); }
      catch (e) { toast(e.message, "error"); }
    });
    return el("tr", {},
      el("td", { text: String(s.phase) }),
      el("td", {}, el("a", { href: s.url, target: "_blank", rel: "noopener noreferrer", text: s.title })),
      el("td", { class: "num-col", text: String(s.duration_min) }),
      el("td", { class: "num-col", text: String(s.weight) }),
      el("td", { class: "num-col", text: TIERS[s.min_tier] }),
      el("td", {}, el("span", { class: "badge" + (s.verified ? " badge-ok" : ""), text: s.verified ? "Verified" : "Pending" })),
      el("td", {}, el("div", { class: "row-actions" }, verify, edit, del)));
  }

  async function save(id, payload, closeAfter = true) {
    try {
      if (id) await api("PUT", `/api/faculty/steps/${id}`, payload);
      else await api("POST", "/api/faculty/steps", { ...payload, stream: current });
      if (closeAfter) dialog.close();
      toast("Saved."); loadSteps(); loadOverview();
    } catch (e) {
      if (closeAfter) { errBox.hidden = false; errBox.textContent = e.message; } else toast(e.message, "error");
    }
  }

  function openDialog(step) {
    editing = step || null; errBox.hidden = true;
    root.querySelector("[data-dialog-title]").textContent = step ? "Edit lesson" : "Add lesson";
    const f = form.elements;  // form.title would return the tooltip text, so use form.elements
    f.title.value = step?.title || ""; f.url.value = step?.url || "";
    f.phase.value = step?.phase || 1; f.duration_min.value = step?.duration_min || 60;
    f.weight.value = step?.weight || 5; f.min_tier.value = step?.min_tier ?? 0;
    f.verified.checked = !!step?.verified;
    dialog.showModal();
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const f = form.elements;
    save(editing?.id, {
      title: f.title.value, url: f.url.value, phase: f.phase.value, duration_min: f.duration_min.value,
      weight: f.weight.value, min_tier: f.min_tier.value, verified: f.verified.checked,
    });
  });
  root.querySelector("[data-cancel]").addEventListener("click", () => dialog.close());
  root.querySelector("[data-add]").addEventListener("click", () => openDialog(null));

  try {
    await loadOverview();
    current = streams[0]?.slug; paintTabs();
    if (current) await loadSteps();
  } catch (e) { toast(e.message, "error"); }
});
