(function () {
  var tabs = document.querySelectorAll("[data-auth-tab]");
  if (!tabs.length) return;

  var panels = {
    login: document.querySelector('[data-auth-panel="login"]'),
    signup: document.querySelector('[data-auth-panel="signup"]'),
  };
  var headings = {
    login: document.querySelector("[data-login-heading]"),
    signup: document.querySelector("[data-signup-heading]"),
  };
  var leads = {
    login: document.querySelector("[data-login-lead]"),
    signup: document.querySelector("[data-signup-lead]"),
  };
  var banner = document.querySelector(".nlv2_bredcrumb_wrapper .banner-content h1");

  function setMode(mode) {
    var signup = mode === "signup";
    tabs.forEach(function (tab) {
      var active = tab.getAttribute("data-auth-tab") === mode;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (panels.login) panels.login.hidden = signup;
    if (panels.signup) panels.signup.hidden = !signup;
    if (headings.login) headings.login.hidden = signup;
    if (headings.signup) headings.signup.hidden = !signup;
    if (leads.login) leads.login.hidden = signup;
    if (leads.signup) leads.signup.hidden = !signup;
    if (banner) banner.textContent = signup ? "Sign up" : "Login";
    var siteTitle = document.title.replace(/^(Login|Sign up)\s*—\s*/, "");
    document.title = (signup ? "Sign up" : "Login") + " — " + siteTitle;

    try {
      var url = new URL(window.location.href);
      if (signup) url.searchParams.set("mode", "signup");
      else url.searchParams.delete("mode");
      window.history.replaceState({}, "", url.pathname + url.search + url.hash);
    } catch (e) {}
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      setMode(tab.getAttribute("data-auth-tab"));
    });
  });
})();
