(function () {
  var store = window.EventRentalStore;
  if (!store) return;

  var emptyEl = document.getElementById("wishEmpty");
  var listEl = document.getElementById("wishList");

  function render() {
    var items = store.wishlist();
    var empty = items.length === 0;
    emptyEl.hidden = !empty;
    listEl.hidden = empty;
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
            '<button type="button" class="bag-add" data-cart="' + item.slug + '">Add to Cart</button>' +
          "</div>" +
          '<button type="button" class="bag-remove" data-remove="' + item.slug + '" aria-label="Remove">×</button>' +
        "</article>"
      );
    }).join("");
  }

  listEl.addEventListener("click", function (event) {
    var removeBtn = event.target.closest("[data-remove]");
    var cartBtn = event.target.closest("[data-cart]");
    if (removeBtn) {
      store.removeWishlist(removeBtn.getAttribute("data-remove"));
      render();
      return;
    }
    if (cartBtn) {
      var slug = cartBtn.getAttribute("data-cart");
      var item = store.wishlist().find(function (entry) { return entry.slug === slug; });
      if (item) store.addToCart({ slug: item.slug, name: item.name, image: item.image, url: item.url, category: item.category, qty: 1 });
    }
  });

  render();
})();
