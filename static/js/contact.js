(function () {
  var form = document.getElementById("contactForm");
  if (!form) return;

  var successEl = document.getElementById("contactSuccess");
  var errorEl = document.getElementById("contactError");
  var submitBtn = document.getElementById("contactSubmit");

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
    ["name", "email", "phone", "message"].forEach(function (name) {
      showFieldError(name, "");
    });
    successEl.style.display = "none";
    errorEl.style.display = "none";
  }

  function collectQuoteItems() {
    var store = window.EventRentalStore;
    var items = store && store.cart ? store.cart() : [];
    if (items.length) {
      return items.map(function (item) {
        return { slug: item.slug || "", name: item.name || "", qty: Number(item.qty) || 1 };
      });
    }
    var params = new URLSearchParams(window.location.search);
    var name = params.get("product") || "";
    var slug = params.get("slug") || "";
    var qty = Number(params.get("qty") || 1) || 1;
    if (slug || name) {
      return [{ slug: slug, name: name, qty: qty }];
    }
    return [];
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors();
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';

    var itemsField = document.getElementById("quoteItems");
    if (itemsField) itemsField.value = JSON.stringify(collectQuoteItems());

    fetch(form.action || "/contact/submit/", {
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
          if (window.EventRentalStore && window.EventRentalStore.clearCart) {
            window.EventRentalStore.clearCart();
          }
        } else {
          var errors = result.data.errors || {};
          Object.keys(errors).forEach(function (key) {
            showFieldError(key, errors[key]);
          });
          errorEl.textContent = result.data.message || "Unable to send your message. Please try again later.";
          errorEl.style.display = "block";
        }
      })
      .catch(function () {
        errorEl.textContent = "Unable to send your message. Please try again later.";
        errorEl.style.display = "block";
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = "Send Message";
      });
  });
})();
