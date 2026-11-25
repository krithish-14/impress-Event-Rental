(function () {
  function samePath(url) {
    try {
      return new URL(url, window.location.href).pathname === window.location.pathname;
    } catch (err) {
      return false;
    }
  }

  function onChangelist() {
    return Boolean(document.getElementById("changelist"));
  }

  document.addEventListener("click", function (event) {
    if (!onChangelist()) return;
    var link = event.target.closest("a");
    if (!link || !link.href) return;
    if (link.target && link.target !== "_self") return;
    var raw = link.getAttribute("href") || "";
    if (!raw || raw.charAt(0) === "#") return;
    if (raw.indexOf("javascript:") === 0) return;
    if (!samePath(link.href)) return;
    event.preventDefault();
    window.location.replace(link.href);
  });

  document.addEventListener("submit", function (event) {
    if (!onChangelist()) return;
    var form = event.target;
    if (form.id === "changelist-form") return;
    var method = (form.getAttribute("method") || "get").toLowerCase();
    if (method !== "get") return;
    var action = form.getAttribute("action") || window.location.pathname;
    var next = new URL(action, window.location.href);
    if (next.pathname !== window.location.pathname) return;
    event.preventDefault();
    var params = new URLSearchParams(new FormData(form));
    var query = params.toString();
    window.location.replace(next.pathname + (query ? "?" + query : ""));
  });
})();
