/* page-dashboard.js - "My learning": continue card, stats, phases, study plan, AI gap analysis. */
document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-dashboard]");
  if (!root) return;
  const { api, el, toast, formatDuration, formatDate, ring } = window.DP;
  const q = (s) => root.querySelector(s);
  const meter = ring(q("[data-ring]"));
  const checkTpl = document.getElementById("tpl-check");
  const check = () => (checkTpl ? checkTpl.content.firstElementChild.cloneNode(true) : document.createTextNode(""));
  let data = null;

  function renderContinue(m) {
    const body = q("[data-continue-body]");
    const n = m.next_step;
    if (!n) {
      body.replaceChildren(
        el("p", { class: "eyebrow", text: "Roadmap complete" }),
        el("h2", { class: "continue-title", text: "You finished every lesson for this tier" }),
        el("p", { class: "muted", text: "Raise your target package to unlock more advanced lessons, or start applying while it is fresh." }),
        el("div", { class: "continue-actions" }, el("a", { class: "btn btn-primary", href: "/setup", text: "Raise my target" })));
      return;
    }
    const phase = m.phases.find((p) => p.phase === n.phase);
    const done = el("button", { class: "btn btn-ghost", type: "button", text: "Mark as done" });
    done.addEventListener("click", async () => {
      done.disabled = true;
      try { await api("POST", `/api/progress/${n.id}`, { done: true }); toast("Nice work. Your meter is updated."); await load(); }
      catch (e) { toast(e.message, "error"); done.disabled = false; }
    });
    body.replaceChildren(
      el("p", { class: "eyebrow", text: `Continue learning · ${n.phase_name}` }),
      el("h2", { class: "continue-title", text: n.title }),
      el("div", { class: "continue-meta" },
        el("span", { text: formatDuration(n.duration_min) }), el("span", { text: `${n.weight} points` }),
        phase ? el("span", { text: `${phase.done} of ${phase.total} lessons done in this phase` }) : null),
      el("div", { class: "progress", role: "img", "aria-label": `Overall progress ${m.percent} percent` }, el("span")),
      el("div", { class: "continue-actions" },
        el("a", { class: "btn btn-primary", href: n.url, target: "_blank", rel: "noopener noreferrer", text: "Watch lesson" }), done,
        el("a", { class: "btn btn-text", href: `/roadmap#phase-${n.phase}`, text: "View curriculum" })));
    body.querySelector(".progress span").style.width = `${m.percent}%`;
  }

  function render(d) {
    data = d;
    const m = d.meter, plan = d.plan;
    q("[data-stream-line]").textContent = `${d.stream.name} · ${d.tier.name} tier · ${d.target_lpa} LPA target`;
    meter.update(m.percent);
    q("[data-label]").textContent = m.label;
    q('[data-stat="lessons"]').textContent = `${m.done_count}/${m.total_count}`;
    q('[data-stat="points"]').textContent = `${m.done_weight} of ${m.total_weight} points`;
    q('[data-stat="hours"]').textContent = m.hours_left;
    const finished = m.total_count > 0 && m.done_count === m.total_count;
    q('[data-stat="finish"]').textContent = finished ? "Complete" : formatDate(plan.finish_date);
    q('[data-stat="pace"]').textContent = finished ? "all lessons done" : `${plan.days_left} days at ${plan.daily_hours} h/day`;

    renderContinue(m);

    q("[data-phases]").replaceChildren(...m.phases.map((p) => {
      const a = el("a", { class: "phase-item", href: `/roadmap#phase-${p.phase}` },
        el("span", { class: "t", text: `${p.phase}. ${p.name}` }),
        el("span", { class: "pct", text: `${Math.round(p.percent)}%` }),
        el("span", { class: "m", text: `${p.done} of ${p.total} lessons` }),
        el("div", { class: "progress progress-sm", role: "img", "aria-label": `${p.name} ${p.percent} percent` }, el("span")));
      a.querySelector(".progress span").style.width = `${p.percent}%`;
      return a;
    }));

    const streak = q("[data-streak]");
    streak.hidden = !d.streak;
    q("[data-streak-text]").textContent = `${d.streak}-day streak`;
    q("[data-pace]").querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", String(parseFloat(c.dataset.hours) === plan.daily_hours)));
    q("[data-plan-note]").textContent = finished ? "You have finished this roadmap." :
      d.active_today ? `Great, you studied today. At ${plan.daily_hours} h/day you finish in about ${plan.days_left} days.` :
      `At ${plan.daily_hours} h/day you finish in about ${plan.days_left} days. Finish a lesson today to ${d.streak ? "keep your streak" : "start a streak"}.`;

    const recent = q("[data-recent]");
    recent.replaceChildren(...(d.recent.length ? d.recent.map((r) =>
      el("li", {}, check(), el("span", {}, r.title, el("small", { text: `Completed ${formatDate(r.completed_on)}` })))) :
      [el("li", { class: "muted small", text: "Nothing yet. Finish your first lesson to see it here." })]));
  }

  async function load() {
    try { render(await api("GET", "/api/roadmap")); }
    catch (e) { if (e.status === 409) window.location.assign("/setup"); else toast(e.message, "error"); }
  }

  q("[data-pace]").querySelectorAll(".chip").forEach((c) => c.addEventListener("click", async () => {
    try { await api("POST", "/api/profile", { daily_hours: parseFloat(c.dataset.hours) }); await load(); toast("Study pace updated."); }
    catch (e) { toast(e.message, "error"); }
  }));

  const gapBtn = q("[data-gap]"), gapOut = q("[data-gap-result]"), gapSrc = q("[data-gap-source]");
  gapBtn.addEventListener("click", async () => {
    gapBtn.disabled = true; gapBtn.classList.add("is-loading");
    try {
      const r = await api("POST", "/api/ai/gap", {});
      gapOut.hidden = false; gapOut.textContent = r.analysis;
      gapSrc.textContent = r.source === "llm" ? "Generated by the AI mentor from your progress data." : "Rule-based analysis from your progress data.";
    } catch (e) { toast(e.message, "error"); }
    finally { gapBtn.disabled = false; gapBtn.classList.remove("is-loading"); }
  });

  load();
});
