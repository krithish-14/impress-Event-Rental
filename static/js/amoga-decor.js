(function () {
  var form = document.getElementById("amogaForm");
  if (!form) return;

  var successEl = document.getElementById("amogaSuccess");
  var errorEl = document.getElementById("amogaError");
  var submitBtn = document.getElementById("amogaSubmit");
  var fields = ["name", "company_name", "event_type", "email", "phone", "decor_details"];

  function showFieldError(name, message) {
    var input = form.querySelector('[name="' + name + '"]');
    var msg = form.querySelector('.error-msg[data-for="' + name + '"]');
    if (input) input.classList.toggle("invalid", Boolean(message));
    if (msg) {
      msg.textContent = message || "";
      msg.style.display = message ? "block" : "none";
    }
  }

  function clearErrors() {
    fields.forEach(function (name) {
      showFieldError(name, "");
    });
    successEl.style.display = "none";
    errorEl.style.display = "none";
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors();
    submitBtn.disabled = true;
    var original = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending…';

    fetch(form.action || "/amoga-decor/submit/", {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: new FormData(form),
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (result.ok && result.data.success) {
          successEl.textContent = result.data.message;
          successEl.style.display = "block";
          form.reset();
          successEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } else {
          var errors = result.data.errors || {};
          Object.keys(errors).forEach(function (key) {
            showFieldError(key, errors[key]);
          });
          errorEl.textContent =
            result.data.message || "Unable to send your enquiry. Please try again later.";
          errorEl.style.display = "block";
        }
      })
      .catch(function () {
        errorEl.textContent = "Unable to send your enquiry. Please try again later.";
        errorEl.style.display = "block";
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.innerHTML = original;
      });
  });
})();
