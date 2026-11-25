(function (window) {
  var CART_KEY = "eventrental_cart";
  var WISH_KEY = "eventrental_wishlist";

  function read(key) {
    try {
      return JSON.parse(window.localStorage.getItem(key) || "[]");
    } catch (err) {
      return [];
    }
  }

  function write(key, items) {
    window.localStorage.setItem(key, JSON.stringify(items));
    updateCounts();
    window.dispatchEvent(new CustomEvent("er-store-change"));
  }

  function countItems(items) {
    return items.reduce(function (sum, item) {
      return sum + (Number(item.qty) || 1);
    }, 0);
  }

  function updateCounts() {
    var cartCount = countItems(read(CART_KEY));
    var wishCount = read(WISH_KEY).length;
    document.querySelectorAll('[data-count="cart"]').forEach(function (el) {
      el.textContent = cartCount;
      el.hidden = cartCount === 0;
    });
    document.querySelectorAll('[data-count="wishlist"]').forEach(function (el) {
      el.textContent = wishCount;
      el.hidden = wishCount === 0;
    });
  }

  function addToCart(item) {
    var items = read(CART_KEY);
    var existing = items.find(function (entry) { return entry.slug === item.slug; });
    var qty = Number(item.qty) || 1;
    if (existing) {
      existing.qty = (Number(existing.qty) || 1) + qty;
    } else {
      items.push({
        slug: item.slug,
        name: item.name,
        image: item.image,
        url: item.url,
        category: item.category || "",
        qty: qty,
      });
    }
    write(CART_KEY, items);
    return items;
  }

  function setCartQty(slug, qty) {
    var items = read(CART_KEY).map(function (item) {
      if (item.slug === slug) item.qty = Math.max(1, Number(qty) || 1);
      return item;
    });
    write(CART_KEY, items);
  }

  function clearCart() {
    write(CART_KEY, []);
  }

  function removeFromCart(slug) {
    write(CART_KEY, read(CART_KEY).filter(function (item) { return item.slug !== slug; }));
  }

  function isWishlisted(slug) {
    return read(WISH_KEY).some(function (item) { return item.slug === slug; });
  }

  function toggleWishlist(item) {
    var items = read(WISH_KEY);
    if (isWishlisted(item.slug)) {
      items = items.filter(function (entry) { return entry.slug !== item.slug; });
    } else {
      items.push({
        slug: item.slug,
        name: item.name,
        image: item.image,
        url: item.url,
        category: item.category || "",
      });
    }
    write(WISH_KEY, items);
    return isWishlisted(item.slug);
  }

  function removeWishlist(slug) {
    write(WISH_KEY, read(WISH_KEY).filter(function (item) { return item.slug !== slug; }));
  }

  window.EventRentalStore = {
    cart: function () { return read(CART_KEY); },
    wishlist: function () { return read(WISH_KEY); },
    addToCart: addToCart,
    setCartQty: setCartQty,
    clearCart: clearCart,
    removeFromCart: removeFromCart,
    isWishlisted: isWishlisted,
    toggleWishlist: toggleWishlist,
    removeWishlist: removeWishlist,
    updateCounts: updateCounts,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateCounts);
  } else {
    updateCounts();
  }
})(window);
