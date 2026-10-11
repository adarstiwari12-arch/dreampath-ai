/* page-roadmap.js - curriculum: sections, tick-able lessons, search, filter, sort, sticky progress. */
document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-roadmap]");
  if (!root) return;
  const { api, el, toast, formatDuration, formatDate, ring } = window.DP;
  const q = (s) => root.querySelector(s);
  const container = q("[data-phases]");
  const search = q("[data-search]");
  const expandBtn = q("[data-expand]");
  const meter = ring(q("[data-ring]"));

  let data = null, filter = "all", sort = "path", query = "";
  const openSections = new Set();
  let allOpen = false;

  const value = (s) => s.weight / (s.duration_min / 60);
  const matches = (s) => !query || s.title.toLowerCase().includes(query);

  function visible(steps) {
    let list = steps.filter((s) => matches(s) && (filter === "all" || (filter === "done" ? s.done : !s.done)));
    if (sort === "value") list = [...list].sort((a, b) => value(b) - value(a));
    return list;
  }

  function renderSide() {
    const m = data.meter, plan = data.plan;
    meter.update(m.percent);
    q("[data-label]").textContent = m.label;
    q('[data-side="lessons"]').textContent = `${m.done_count}/${m.total_count}`;
    q('[data-side="hours"]').textContent = `${m.hours_left} h`;
    q('[data-side="finish"]').textContent = m.done_count === m.total_count ? "Complete" : formatDate(plan.finish_date);
    const card = q("[data-next-card]");
    const n = m.next_step;
    card.hidden = !n;
    if (n) {
      q("[data-next-title]").textContent = n.title;
      q("[data-next-meta]").textContent = `${n.phase_name} · ${formatDuration(n.duration_min)} · ${n.weight} points`;
      q("[data-next-link]").href = n.url;
    }
  }

  function lessonRow(s, nextId) {
    const id = `step-${s.id}`;
    const box = el("input", { type: "checkbox", id, class: "lesson-check", checked: s.done, "aria-label": `Mark ${s.title} as done` });
    box.addEventListener("change", () => toggle(s, box));
    return el("li", { class: "lesson" + (s.done ? " is-done" : "") + (s.id === nextId ? " is-next" : "") },
      box,
      el("div", {},
        el("p", { class: "lesson-title" },
          el("span", { class: "t", text: s.title }),
          s.id === nextId ? el("span", { class: "badge badge-brand", text: "Up next" }) : null,
          s.verified ? el("span", { class: "badge badge-ok", text: "Verified" }) : null),
        el("div", { class: "lesson-meta" },
          el("span", { text: formatDuration(s.duration_min) }),
          el("span", { text: `${s.weight} pts` }),
          el("span", { text: `${value(s).toFixed(1)} pts/hour` }))),
      el("a", { class: "btn btn-ghost btn-sm", href: s.url, target: "_blank", rel: "noopener noreferrer", text: "Watch" }));
  }

  function render() {
    renderSide();
    const nextId = data.meter.next_step?.id;
    const sections = data.phases.map((phase) => {
      const total = phase.steps.reduce((a, s) => a + s.weight, 0);
      const done = phase.steps.reduce((a, s) => a + (s.done ? s.weight : 0), 0);
      const pct = total ? (done / total) * 100 : 0;
      const minutes = phase.steps.reduce((a, s) => a + s.duration_min, 0);
      const items = visible(phase.steps);
      const forceOpen = (query || filter !== "all") && items.length > 0;
      const section = el("details", { class: "section-card", id: `phase-${phase.phase}`, open: allOpen || forceOpen || openSections.has(phase.phase) },
        el("summary", {},
          el("span", { class: "section-title", text: `${phase.phase}. ${phase.name}` }),
          el("span", { class: "section-meta", text: `${phase.steps.filter((s) => s.done).length} of ${phase.steps.length} lessons · ${formatDuration(minutes)} · ${Math.round(pct)}%` }),
          el("div", { class: "progress progress-sm" }, el("span"))),
        items.length ? el("ul", { class: "lessons" }, items.map((s) => lessonRow(s, nextId)))
                     : el("p", { class: "empty", text: query ? "No lessons match your search here." : filter === "done" ? "Nothing ticked in this phase yet." : "All done here. Nice." }));
      section.addEventListener("toggle", () => { section.open ? openSections.add(phase.phase) : openSections.delete(phase.phase); });
      section.querySelector(".progress span").style.width = `${pct}%`;
      return section;
    });
    container.replaceChildren(...sections);
  }

  async function toggle(step, box) {
    const wanted = box.checked;
    box.disabled = true;
    try {
      const r = await api("POST", `/api/progress/${step.id}`, { done: wanted });
      step.done = wanted;
      Object.assign(data, { meter: r.meter, plan: r.plan, streak: r.streak, recent: r.recent });
      render();
      document.getElementById(`step-${step.id}`)?.focus();  // keep the keyboard position after re-render
      if (wanted) toast(r.streak > 1 ? `Lesson complete. ${r.streak}-day streak!` : "Lesson complete.");
    } catch (e) {
      box.checked = !wanted; toast(e.message, "error");
    } finally { box.disabled = false; }
  }

  q("[data-filter]") && root.querySelectorAll("[data-filter]").forEach((b) => b.addEventListener("click", () => {
    filter = b.dataset.filter;
    root.querySelectorAll("[data-filter]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    render();
  }));
  q("[data-sort]").addEventListener("change", (e) => { sort = e.target.value; render(); });
  search.addEventListener("input", () => { query = search.value.trim().toLowerCase(); render(); });
  expandBtn.addEventListener("click", () => {
    allOpen = !allOpen; expandBtn.textContent = allOpen ? "Collapse all" : "Expand all";
    if (!allOpen) openSections.clear();
    render();
  });

  (async () => {
    try {
      data = await api("GET", "/api/roadmap");
      q("[data-subtitle]").textContent = `${data.stream.name} · ${data.tier.name} tier · ${data.target_lpa} LPA`;
      const n = data.meter.next_step;
      if (n) openSections.add(n.phase); else openSections.add(1);
      const hash = window.location.hash.match(/^#phase-(\d)$/);
      if (hash) openSections.add(Number(hash[1]));
      const initial = new URLSearchParams(window.location.search).get("q");
      if (initial) { search.value = initial.slice(0, 80); query = search.value.trim().toLowerCase(); }
      render();
      if (hash) document.getElementById(`phase-${hash[1]}`)?.scrollIntoView({ block: "start" });
    } catch (e) {
      if (e.status === 409) window.location.assign("/setup"); else toast(e.message, "error");
    }
  })();
});
