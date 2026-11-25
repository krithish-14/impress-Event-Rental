(function () {
  function csrfToken() {
    var input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input && input.value) return input.value;
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".er-row-delete");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();

    var name = button.getAttribute("data-name") || "this product";
    var url = button.getAttribute("data-url");
    if (!url) return;

    var ok = window.confirm(
      'Remove "' + name + '" from the website?\n\nClick OK to delete, or Cancel to keep it.'
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
        if (!response.ok) throw new Error("Delete failed");
        return response.json();
      })
      .then(function () {
        window.location.reload();
      })
      .catch(function () {
        button.disabled = false;
        window.alert("Could not remove this product. Please try again.");
      });
  });
})();
