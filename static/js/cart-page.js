(function () {
  var store = window.EventRentalStore;
  if (!store) return;

  var emptyEl = document.getElementById("cartEmpty");
  var listEl = document.getElementById("cartList");
  var footerEl = document.getElementById("cartFooter");
  var totalEl = document.getElementById("cartTotal");
  var quoteBtn = document.getElementById("cartQuoteBtn");
  var whatsappBtn = document.getElementById("cartWhatsappBtn");
  var whatsappNumber = (whatsappBtn && whatsappBtn.href.match(/wa\.me\/([^?]+)/) || [])[1] || "";

  function render() {
    var items = store.cart();
    var empty = items.length === 0;
    emptyEl.hidden = !empty;
    listEl.hidden = empty;
    footerEl.hidden = empty;
    if (empty) {
      listEl.innerHTML = "";
      return;
    }

    listEl.innerHTML = items.map(function (item) {
      return (
        '<article class="bag-item" data-slug="' + item.slug + '">' +
          '<a class="bag-thumb" href="' + item.url + '"><img src="' + item.image + '" alt="' + item.name + '"></a>' +
          '<div class="bag-info">' +
            '<p class="bag-cat">' + (item.category || "") + "</p>" +
            '<a href="' + item.url + '"><h3>' + item.name + "</h3></a>" +
            '<label>Qty <input type="number" min="1" value="' + item.qty + '" data-qty="' + item.slug + '"></label>' +
          "</div>" +
          '<button type="button" class="bag-remove" data-remove="' + item.slug + '" aria-label="Remove">×</button>' +
        "</article>"
      );
    }).join("");

    var count = items.reduce(function (sum, item) { return sum + (Number(item.qty) || 1); }, 0);
    totalEl.textContent = count;
    var names = items.map(function (item) { return item.name + " x" + item.qty; }).join(", ");
    quoteBtn.href = "/contact/?product=" + encodeURIComponent(names);
    if (whatsappBtn && whatsappNumber) {
      var message =
        "Hi, I would like a rental enquiry for these items: " +
        names +
        ".";
      whatsappBtn.href =
        "https://wa.me/" + whatsappNumber + "?text=" + encodeURIComponent(message);
    }
  }

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
      render();
    }
  });

  render();
})();
