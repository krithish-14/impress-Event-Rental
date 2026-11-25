(function () {
  function preferredTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function currentTheme() {
    var stored = localStorage.getItem("theme");
    if (stored === "dark" || stored === "light") return stored;
    return preferredTheme();
  }

  function setTheme(mode) {
    document.documentElement.setAttribute("data-theme", mode);
    localStorage.setItem("theme", mode);
    document.querySelectorAll(".theme-toggle").forEach(function (button) {
      var toDark = mode !== "dark";
      button.setAttribute("aria-label", toDark ? "Switch to dark theme" : "Switch to light theme");
      button.setAttribute("title", toDark ? "Dark theme" : "Light theme");
    });
  }

  function toggleTheme(event) {
    event.preventDefault();
    setTheme(currentTheme() === "dark" ? "light" : "dark");
  }

  setTheme(currentTheme());

  function bind() {
    document.querySelectorAll(".theme-toggle").forEach(function (button) {
      button.addEventListener("click", toggleTheme);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
