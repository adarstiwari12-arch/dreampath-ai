/* page-setup.js - stream, package and pace selection with a live plan summary. */
document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-setup]");
  if (!root) return;
  const { api, el, toast, formatDate } = window.DP;

  const picks = [...root.querySelectorAll(".pick")];
  const slider = document.getElementById("lpa");
  const lpaValue = root.querySelector("[data-lpa-value]");
  const tierBlurb = root.querySelector("[data-tier-blurb]");
  const tierPills = [...root.querySelectorAll(".tier-pill")];
  const chips = [...root.querySelectorAll("[data-pace] .chip")];
  const summary = root.querySelector("[data-summary]");
  const save = root.querySelector("[data-save]");
  const stepInd = (k) => root.querySelector(`[data-step-ind="${k}"]`);

  const TIER_NAMES = tierPills.map((p) => p.querySelector("strong").textContent);
  const TIER_BLURBS = [
    "Solid fundamentals and a clean resume for core and service roles.",
    "Stronger core subjects, tools and projects for product and mid-tier roles.",
    "Depth, design thinking and specialisation for top product companies.",
    "Advanced and research-grade skills for the most competitive offers.",
  ];
  const tierOf = (lpa) => tierPills.reduce((t, p, i) => (lpa >= Number(p.dataset.min) ? i : t), 0);

  const known = new Set(picks.map((p) => p.dataset.slug));
  let slug = known.has(root.dataset.slug) ? root.dataset.slug : "";
  let pace = parseFloat(root.dataset.pace) || 1.5;

  function render() {
    const lpa = parseFloat(slider.value);
    const tier = tierOf(lpa);
    lpaValue.textContent = Number.isInteger(lpa) ? String(lpa) : lpa.toFixed(1);
    tierBlurb.textContent = `${TIER_NAMES[tier]} tier. ${TIER_BLURBS[tier]}`;
    tierPills.forEach((p, i) => p.classList.toggle("is-active", i === tier));
    picks.forEach((p) => p.setAttribute("aria-pressed", String(p.dataset.slug === slug)));
    chips.forEach((c) => c.setAttribute("aria-pressed", String(parseFloat(c.dataset.hours) === pace)));

    stepInd("stream").classList.toggle("is-done", !!slug);
    stepInd("package").classList.toggle("is-done", !!slug);
    stepInd("pace").classList.toggle("is-done", !!slug);
    save.disabled = !slug;

    const pick = picks.find((p) => p.dataset.slug === slug);
    if (!pick) { summary.textContent = "Choose a stream to see your plan."; return; }
    const lessons = Number(pick.dataset.lessons.split(",")[tier]);
    const hours = Number(pick.dataset.minutes.split(",")[tier]) / 60;
    const finish = new Date(); finish.setDate(finish.getDate() + Math.ceil(hours / pace));
    const iso = `${finish.getFullYear()}-${String(finish.getMonth() + 1).padStart(2, "0")}-${String(finish.getDate()).padStart(2, "0")}`;
    summary.replaceChildren(
      el("strong", { text: pick.dataset.name }),
      ` · ${lpaValue.textContent} LPA · ${TIER_NAMES[tier]} tier · ${lessons} lessons · ${Math.round(hours)} h · finish by ${formatDate(iso)}`);
  }

  picks.forEach((p) => p.addEventListener("click", () => { slug = p.dataset.slug; render(); }));
  chips.forEach((c) => c.addEventListener("click", () => { pace = parseFloat(c.dataset.hours); render(); }));
  slider.addEventListener("input", render);
  const lpa0 = parseFloat(root.dataset.lpa);
  if (lpa0) slider.value = String(lpa0);

  // AI stream suggestion
  const recBtn = root.querySelector("[data-recommend]");
  const recOut = root.querySelector("[data-recommend-result]");
  recBtn.addEventListener("click", async () => {
    recBtn.disabled = true; recOut.textContent = "Thinking...";
    try {
      const r = await api("POST", "/api/ai/recommend-stream", { interests: document.getElementById("interests").value });
      slug = r.stream; render();
      const name = picks.find((p) => p.dataset.slug === r.stream)?.dataset.name || r.stream;
      recOut.textContent = `Suggested: ${name}. ${r.reason}${r.source === "rules" ? " (rule-based suggestion)" : ""}`;
    } catch (e) { recOut.textContent = e.message; }
    finally { recBtn.disabled = false; }
  });

  save.addEventListener("click", async () => {
    save.disabled = true; save.classList.add("is-loading");
    try {
      await api("POST", "/api/profile", { stream: slug, target_lpa: parseFloat(slider.value), daily_hours: pace });
      window.location.assign(root.dataset.next || "/dashboard");
    } catch (e) {
      toast(e.message, "error"); save.disabled = false; save.classList.remove("is-loading");
    }
  });

  render();
});
