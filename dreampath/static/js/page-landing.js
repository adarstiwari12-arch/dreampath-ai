/* page-landing.js - interactive Dream Meter demo on the landing page. */
document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-demo]");
  if (!root) return;
  const { el, ring } = window.DP;
  const lessons = [
    { title: "Data structures and algorithms", weight: 10, done: true },
    { title: "Build a full stack project", weight: 8, done: true },
    { title: "DBMS and SQL", weight: 7, done: false },
    { title: "Operating systems fundamentals", weight: 6, done: false },
    { title: "Resume building", weight: 4, done: false },
  ];
  const meter = ring(root.querySelector("[data-ring]"));
  const list = root.querySelector("[data-demo-list]");
  const note = root.querySelector("[data-demo-formula]");
  const total = lessons.reduce((a, s) => a + s.weight, 0);

  function refresh() {
    const done = lessons.reduce((a, s) => a + (s.done ? s.weight : 0), 0);
    meter.update((done / total) * 100);
    note.textContent = `${done} of ${total} weight points ticked = ${Math.round((done / total) * 1000) / 10}%`;
  }

  lessons.forEach((s, i) => {
    const id = `demo-${i}`;
    const input = el("input", { type: "checkbox", id, checked: s.done });
    input.addEventListener("change", () => { s.done = input.checked; refresh(); });
    list.append(el("li", {}, el("label", { for: id }, input, el("span", { text: s.title }), el("span", { class: "w", text: `${s.weight} pts` }))));
  });
  refresh();
});
