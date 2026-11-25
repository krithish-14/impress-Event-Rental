(function () {
  var store = window.EventRentalStore;
  var grid = document.getElementById("product-grid");
  if (!store || !grid) return;

  function itemFromButton(button) {
    return {
      slug: button.getAttribute("data-slug"),
      name: button.getAttribute("data-name"),
      image: button.getAttribute("data-image"),
      url: button.getAttribute("data-url"),
      category: button.getAttribute("data-category") || "",
      qty: 1,
    };
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
    var button = event.target.closest(".card-wish-btn");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    store.toggleWishlist(itemFromButton(button));
    syncHearts();
  });

  syncHearts();
})();
