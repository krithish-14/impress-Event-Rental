(function () {
  var ICONS = {
    delete_selected:
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h5v2H3V5h5l1-2zm1 6h2v10h-2V9zm4 0h2v10h-2V9zM7 9h2v10H7V9zm-1 12h12l1-12H5l1 12z"/></svg>',
    mark_read:
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z"/></svg>',
    mark_unread:
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 12H4V8l8 5 8-5v8zm-8-5L4 6h16l-8 5z"/></svg>',
    mark_rented:
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M13 3a9 9 0 1 0 9 9h-2a7 7 0 1 1-7-7V3zm4.24 4.76 1.42-1.42A8.96 8.96 0 0 1 22 12h-2c0-1.54-.5-2.96-1.34-4.1l-1.42 1.42zM11 7h2v6h-2V7z"/></svg>',
    mark_available:
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
    accept_quotes:
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
  };

  var FALLBACK =
    '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0-6v2a8 8 0 0 0 0 16v2c5.52 0 10-4.48 10-10S17.52 2 12 2z"/></svg>';

  function selectedCount(form) {
    return form.querySelectorAll("input.action-select:checked").length;
  }

  function setup() {
    var form = document.getElementById("changelist-form");
    var changelist = document.getElementById("changelist");
    if (!form || !changelist) return;
    if (document.querySelector(".er-action-icons")) return;

    var select = form.querySelector("select[name='action']");
    if (!select) return;

    var icons = document.createElement("div");
    icons.className = "er-action-icons";
    icons.setAttribute("role", "group");
    icons.setAttribute("aria-label", "Table actions");

    Array.prototype.forEach.call(select.options, function (option) {
      if (!option.value) return;
      var button = document.createElement("button");
      button.type = "button";
      button.className = "er-icon-btn";
      if (option.value === "delete_selected") button.classList.add("is-danger");
      button.setAttribute("data-admin-action", option.value);
      button.title = option.text.replace(/^-+$/, "").trim() || option.value;
      button.setAttribute("aria-label", button.title);
      button.innerHTML = ICONS[option.value] || FALLBACK;
      icons.appendChild(button);
    });

    if (!icons.childNodes.length) return;

    var count = document.createElement("span");
    count.className = "er-action-count";
    icons.insertBefore(count, icons.firstChild);

    function syncCount() {
      var src = form.querySelector(".action-counter");
      count.textContent = src ? src.textContent : "";
    }
    syncCount();
    form.addEventListener("change", syncCount);
    form.addEventListener("click", function () {
      window.setTimeout(syncCount, 0);
    });

    var wrap = document.createElement("div");
    wrap.className = "er-changelist-toolbar";
    var toolbar = document.getElementById("toolbar");
    var host = document.querySelector(".changelist-form-container");
    if (toolbar && toolbar.parentNode) {
      toolbar.parentNode.insertBefore(wrap, toolbar);
      wrap.appendChild(toolbar);
      wrap.appendChild(icons);
    } else if (host) {
      host.insertBefore(wrap, host.firstChild);
      wrap.appendChild(icons);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-admin-action]");
    if (!button) return;
    event.preventDefault();

    var form = document.getElementById("changelist-form");
    if (!form) return;
    var select = form.querySelector("select[name='action']");
    if (!select) return;

    var action = button.getAttribute("data-admin-action");
    if (!selectedCount(form)) {
      window.alert("Select one or more rows first.");
      return;
    }

    select.value = action;
    if (!form.querySelector("[name='index']")) {
      var index = document.createElement("input");
      index.type = "hidden";
      index.name = "index";
      index.value = "0";
      form.appendChild(index);
    }
    form.submit();
  });
})();
