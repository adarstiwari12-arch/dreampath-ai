/* theme.js - Early theme initialization to prevent flash of wrong theme. */
(function () {
  try {
    var saved = localStorage.getItem("color-scheme");
    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var scheme = saved || (prefersDark ? "dark" : "light");
    document.documentElement.setAttribute("data-color-scheme", scheme);
  } catch (e) {
    /* localStorage may be restricted */
  }
})();
