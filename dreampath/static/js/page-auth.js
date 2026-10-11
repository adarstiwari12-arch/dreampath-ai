/* page-auth.js - password visibility, live password hints and confirm check on auth forms. */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    const input = document.getElementById(btn.dataset.togglePassword);
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
    });
  });

  const pw = document.getElementById("password");
  const hint = document.querySelector("[data-pw-hint]");
  const bar = document.querySelector("[data-pw-bar]");
  if (pw && hint && bar) {
    const colours = ["var(--danger)", "var(--danger)", "var(--accent)", "var(--success)", "var(--success)"];
    pw.addEventListener("input", () => {
      const v = pw.value;
      let score = 0;
      if (v.length >= 8) score++;
      if (/[A-Za-z]/.test(v) && /\d/.test(v)) score++;
      if (v.length >= 12) score++;
      if (/[^A-Za-z0-9]/.test(v) || (/[a-z]/.test(v) && /[A-Z]/.test(v))) score++;
      bar.style.width = `${(score / 4) * 100}%`;
      bar.style.background = colours[score];
      const ok = v.length >= 8 && /[A-Za-z]/.test(v) && /\d/.test(v);
      hint.className = "hint" + (v ? (ok ? " is-good" : " is-bad") : "");
      hint.textContent = ok ? "Looks good." : "At least 8 characters, with a letter and a number.";
    });
  }

  const form = document.querySelector("[data-auth-form]");
  const confirm = document.getElementById("confirm");
  if (form && pw && confirm) {
    form.addEventListener("submit", (e) => {
      if (pw.value !== confirm.value) {
        e.preventDefault();
        confirm.focus();
        window.DP.toast("The two passwords do not match.", "error");
      }
    });
  }
});
