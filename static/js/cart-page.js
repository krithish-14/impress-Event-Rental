(function () {
  var store = window.EventRentalStore;
  var cfg = window.EVENT_RENTAL_CART || {};
  if (!store) return;

  var emptyEl = document.getElementById("cartEmpty");
  var filledEl = document.getElementById("cartFilled");
  var listEl = document.getElementById("cartList");
  var totalEl = document.getElementById("cartTotal");
  var form = document.getElementById("cartQuoteForm");
  var quoteBtn = document.getElementById("cartQuoteBtn");
  var whatsappBtn = document.getElementById("cartWhatsappBtn");
  var statusEl = document.getElementById("cartQuoteStatus");
  var emptyStatusEl = document.getElementById("cartEmptyStatus");
  var emptyTitleEl = document.getElementById("cartEmptyTitle");
  var emptyTextEl = document.getElementById("cartEmptyText");
  var csrfInput = form ? form.querySelector("[name=csrfmiddlewaretoken]") : null;

  function csrfToken() {
    if (csrfInput && csrfInput.value) return csrfInput.value;
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function clearErrors() {
    if (!form) return;
    form.querySelectorAll(".error-msg").forEach(function (el) {
      el.textContent = "";
      el.classList.remove("is-visible");
    });
    form.querySelectorAll(".invalid").forEach(function (el) {
      el.classList.remove("invalid");
    });
  }

  function showErrors(errors) {
    Object.keys(errors || {}).forEach(function (key) {
      var field = form.querySelector('[name="' + key + '"]');
      var msg = form.querySelector('[data-error="' + key + '"]');
      if (field) field.classList.add("invalid");
      if (msg) {
        msg.textContent = errors[key];
        msg.classList.add("is-visible");
      }
    });
  }

  function setFormStatus(message, ok) {
    if (!statusEl) return;
    statusEl.hidden = !message;
    statusEl.textContent = message || "";
    statusEl.classList.toggle("is-success", !!ok);
    statusEl.classList.toggle("is-error", !!message && !ok);
  }

  function resetFormFields() {
    if (!form) return;
    form.reset();
    var days = document.getElementById("cartEventDays");
    if (days) days.value = "1";
    clearErrors();
    setFormStatus("", false);
  }

  function showEmptySuccess(message) {
    if (emptyTitleEl) emptyTitleEl.textContent = "Request sent";
    if (emptyTextEl) {
      emptyTextEl.textContent =
        "Your cart is clear. Add more rentals anytime to send another quote.";
    }
    if (emptyStatusEl) {
      emptyStatusEl.hidden = !message;
      emptyStatusEl.textContent = message || "";
    }
  }

  function showDefaultEmpty() {
    if (emptyTitleEl) emptyTitleEl.textContent = "Your cart is empty";
    if (emptyTextEl) {
      emptyTextEl.textContent =
        "Add rentals from any collection to request a quote.";
    }
    if (emptyStatusEl) {
      emptyStatusEl.hidden = true;
      emptyStatusEl.textContent = "";
    }
  }

  function formPayload(source) {
    var items = store.cart().map(function (item) {
      return {
        slug: item.slug,
        name: item.name,
        qty: Number(item.qty) || 1,
      };
    });
    return {
      name: (document.getElementById("cartName") || {}).value || "",
      company_name: (document.getElementById("cartCompany") || {}).value || "",
      phone: (document.getElementById("cartPhone") || {}).value || "",
      email: (document.getElementById("cartEmail") || {}).value || "",
      event_date: (document.getElementById("cartEventDate") || {}).value || "",
      event_days: (document.getElementById("cartEventDays") || {}).value || "",
      message: (document.getElementById("cartMessage") || {}).value || "",
      source: source || "website",
      quote_items: JSON.stringify(items),
      items: items,
    };
  }

  function buildWhatsAppText(data) {
    var items = (data.items || [])
      .map(function (item) {
        return "- " + item.name + " x" + (item.qty || 1);
      })
      .join("\n");
    return (
      "Hi, I would like a rental enquiry.\n\n" +
      "Name: " +
      data.name +
      "\n" +
      (data.company_name ? "Company: " + data.company_name + "\n" : "") +
      "Phone: " +
      data.phone +
      "\n" +
      "Email: " +
      data.email +
      "\n" +
      "Event date: " +
      data.event_date +
      "\n" +
      "Days needed: " +
      data.event_days +
      "\n\n" +
      "Cart items:\n" +
      items +
      "\n\nMessage:\n" +
      data.message
    );
  }

  function setBusy(busy) {
    if (quoteBtn) quoteBtn.disabled = busy;
    if (whatsappBtn) whatsappBtn.disabled = busy;
  }

  function finishSuccess(message) {
    store.clearCart();
    if (typeof store.updateCounts === "function") store.updateCounts();
    resetFormFields();
    showEmptySuccess(message);
    render();
  }

  function submitQuote(source) {
    clearErrors();
    setFormStatus("", false);

    if (!store.cart().length) {
      render();
      return Promise.resolve(null);
    }

    var data = formPayload(source);
    var body = new URLSearchParams();
    Object.keys(data).forEach(function (key) {
      if (key === "items") return;
      body.append(key, data[key]);
    });

    setBusy(true);
    return fetch(cfg.submitUrl || "/cart/quote/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: body,
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          return { ok: response.ok, payload: payload };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          showErrors((result.payload && result.payload.errors) || {});
          setFormStatus(
            (result.payload && result.payload.message) ||
              "Please correct the highlighted fields.",
            false
          );
          return null;
        }
        return { data: data, payload: result.payload };
      })
      .catch(function () {
        setFormStatus("Could not send your request. Please try again.", false);
        return null;
      })
      .finally(function () {
        setBusy(false);
      });
  }

  function render() {
    var items = store.cart();
    var empty = !items.length;

    if (emptyEl) emptyEl.hidden = !empty;
    if (filledEl) filledEl.hidden = empty;

    if (empty) {
      if (listEl) listEl.innerHTML = "";
      if (totalEl) totalEl.textContent = "0";
      return;
    }

    showDefaultEmpty();
    listEl.innerHTML = items
      .map(function (item) {
        return (
          '<article class="bag-item" data-slug="' +
          item.slug +
          '">' +
          '<a class="bag-thumb" href="' +
          item.url +
          '"><img src="' +
          item.image +
          '" alt="' +
          item.name +
          '"></a>' +
          '<div class="bag-info">' +
          '<p class="bag-cat">' +
          (item.category || "") +
          "</p>" +
          '<a href="' +
          item.url +
          '"><h3>' +
          item.name +
          "</h3></a>" +
          '<label>Qty <input type="number" min="1" max="9999" value="' +
          item.qty +
          '" data-qty="' +
          item.slug +
          '"></label>' +
          "</div>" +
          '<button type="button" class="bag-remove" data-remove="' +
          item.slug +
          '" aria-label="Remove">×</button>' +
          "</article>"
        );
      })
      .join("");

    var count = items.reduce(function (sum, item) {
      return sum + (Number(item.qty) || 1);
    }, 0);
    totalEl.textContent = count;
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      submitQuote("website").then(function (result) {
        if (!result) return;
        finishSuccess(
          (result.payload && result.payload.message) ||
            "Quote sent. Our team will contact you shortly."
        );
      });
    });
  }

  if (whatsappBtn) {
    whatsappBtn.addEventListener("click", function () {
      submitQuote("whatsapp").then(function (result) {
        if (!result) return;
        var text = buildWhatsAppText(result.data);
        var number = cfg.whatsapp || "";
        var url =
          "https://wa.me/" + number + "?text=" + encodeURIComponent(text);
        window.open(url, "_blank", "noopener,noreferrer");
        finishSuccess(
          (result.payload && result.payload.message) ||
            "Enquiry saved. WhatsApp is opening…"
        );
      });
    });
  }

  if (listEl) {
    listEl.addEventListener("change", function (event) {
      var slug = event.target.getAttribute("data-qty");
      if (slug) {
        store.setCartQty(slug, event.target.value);
        render();
      }
    });

    listEl.addEventListener("click", function (event) {
      var removeBtn = event.target.closest("[data-remove]");
      if (removeBtn) {
        store.removeFromCart(removeBtn.getAttribute("data-remove"));
        if (!store.cart().length) showDefaultEmpty();
        render();
      }
    });
  }

  render();
})();
