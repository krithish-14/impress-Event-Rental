(function () {
  function csrfToken() {
    var input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input && input.value) return input.value;
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  document.addEventListener("click", function (event) {
    var complete = event.target.closest(".er-complete-btn");
    if (complete) {
      event.preventDefault();
      event.stopPropagation();
      var completeName = complete.getAttribute("data-name") || "this rental";
      var completeUrl = complete.getAttribute("data-url");
      if (!completeUrl) return;
      if (!window.confirm('Mark the rental for "' + completeName + '" complete?\n\nItems will return to live stock. The customer can then write a verified review.')) {
        return;
      }
      complete.disabled = true;
      fetch(completeUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok && data.ok, message: data.message };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            complete.disabled = false;
            window.alert(result.message || "Could not complete this rental.");
            return;
          }
          window.location.reload();
        })
        .catch(function () {
          complete.disabled = false;
          window.alert("Could not complete this rental. Please try again.");
        });
      return;
    }

    var button = event.target.closest(".er-accept-btn");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();

    var name = button.getAttribute("data-name") || "this quote";
    var url = button.getAttribute("data-url");
    if (!url) return;

    var ok = window.confirm(
      'Accept quote from "' + name + '"?\n\nLive stock will decrease and these products will move to rented stock.'
    );
    if (!ok) return;

    button.disabled = true;
    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok && data.ok, message: data.message };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          button.disabled = false;
          window.alert(result.message || "Could not accept this quote.");
          return;
        }
        window.location.reload();
      })
      .catch(function () {
        button.disabled = false;
        window.alert("Could not accept this quote. Please try again.");
      });
  });
})();
