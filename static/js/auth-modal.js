(function () {
  var modal = document.getElementById("authModal");
  if (!modal || window.EVENT_RENTAL_AUTHED) return;

  var loginBtn = document.getElementById("authModalLogin");
  var signupBtn = document.getElementById("authModalSignup");
  var lead = modal.querySelector(".auth-lead");
  var loginBase = loginBtn ? loginBtn.getAttribute("href") : "/login/";
  var signupBase = signupBtn ? signupBtn.getAttribute("href") : "/signup/";
  var defaultLead = lead ? lead.textContent : "";

  function withNext(base, nextUrl) {
    if (!nextUrl) return base;
    return base + (base.indexOf("?") === -1 ? "?" : "&") + "next=" + encodeURIComponent(nextUrl);
  }

  function openAuth(nextUrl, message) {
    var next = nextUrl || window.location.pathname + window.location.search + window.location.hash;
    if (loginBtn) loginBtn.setAttribute("href", withNext(loginBase, next));
    if (signupBtn) signupBtn.setAttribute("href", withNext(signupBase, next));
    if (lead) lead.textContent = message || defaultLead;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeAuth() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  modal.addEventListener("click", function (event) {
    if (event.target.closest("[data-auth-close]")) closeAuth();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) closeAuth();
  });

  window.EventRentalAuth = { open: openAuth, close: closeAuth };
})();
