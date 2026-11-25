(function () {
  var store = window.EventRentalStore;
  var grid = document.getElementById("product-grid");
  if (!store || !grid) return;

  var MAX_QTY = 20;

  function itemFromCard(card, qty) {
    return {
      slug: card.getAttribute("data-slug"),
      name: card.getAttribute("data-name"),
      image: card.getAttribute("data-image"),
      url: card.getAttribute("data-url"),
      category: card.getAttribute("data-category") || "",
      qty: qty,
    };
  }

  function clampQty(value) {
    var qty = parseInt(value, 10);
    if (isNaN(qty) || qty < 1) qty = 1;
    if (qty > MAX_QTY) qty = MAX_QTY;
    return qty;
  }

  function readQty(card) {
    var input = card.querySelector(".card-qty-input");
    return clampQty(input ? input.value : 1);
  }

  function setQty(card, value) {
    var input = card.querySelector(".card-qty-input");
    if (!input) return;
    input.value = String(clampQty(value));
  }

  function syncHearts() {
    grid.querySelectorAll(".card-wish-btn").forEach(function (button) {
      var saved = store.isWishlisted(button.getAttribute("data-slug"));
      button.classList.toggle("is-active", saved);
      var icon = button.querySelector("i");
      if (icon) icon.className = saved ? "fa-solid fa-heart" : "fa-regular fa-heart";
      button.setAttribute("aria-pressed", saved ? "true" : "false");
    });
  }

  grid.addEventListener("click", function (event) {
    var wishBtn = event.target.closest(".card-wish-btn");
    if (wishBtn) {
      event.preventDefault();
      event.stopPropagation();
      store.toggleWishlist(itemFromCard(wishBtn, 1));
      syncHearts();
      return;
    }

    var qtyBtn = event.target.closest(".card-qty-btn");
    if (qtyBtn) {
      event.preventDefault();
      var card = qtyBtn.closest(".product-card");
      if (!card) return;
      var delta = Number(qtyBtn.getAttribute("data-qty-delta")) || 0;
      setQty(card, readQty(card) + delta);
      return;
    }

    var cartBtn = event.target.closest(".card-add-cart");
    if (cartBtn) {
      event.preventDefault();
      var productCard = cartBtn.closest(".product-card");
      if (!productCard) return;
      store.addToCart(itemFromCard(productCard, readQty(productCard)));
      store.updateCounts();
      cartBtn.classList.add("is-added");
      cartBtn.textContent = "Added";
      window.setTimeout(function () {
        cartBtn.classList.remove("is-added");
        cartBtn.textContent = "Add to cart";
      }, 1200);
    }
  });

  grid.addEventListener("change", function (event) {
    var input = event.target.closest(".card-qty-input");
    if (!input) return;
    var card = input.closest(".product-card");
    if (card) setQty(card, input.value);
  });

  grid.addEventListener("keydown", function (event) {
    var input = event.target.closest(".card-qty-input");
    if (!input) return;
    if (event.key === "Enter") {
      event.preventDefault();
      input.blur();
    }
  });

  syncHearts();
})();
