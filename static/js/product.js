(function () {
  var cfg = window.EVENT_RENTAL_PDP;
  if (!cfg) return;

  var qty = document.getElementById("pdp-qty");
  var minusBtn = document.getElementById("pdpQtyMinus");
  var plusBtn = document.getElementById("pdpQtyPlus");
  var cartBtn = document.getElementById("pdpCartBtn");
  var wishBtn = document.getElementById("pdpWishBtn");
  var waBtn = document.getElementById("pdpWhatsappBtn");
  var mainImg = document.getElementById("pdpMainImg");
  var lightbox = document.getElementById("pdpLightbox");
  var closeBtn = document.getElementById("pdpLightboxClose");
  var minQty = qty ? Math.max(1, parseInt(qty.getAttribute("min"), 10) || 1) : 1;
  var maxQty = qty ? Math.max(minQty, parseInt(qty.getAttribute("max"), 10) || 20) : 20;
  var cartResetTimer = null;

  function store() {
    return window.EventRentalStore || null;
  }

  function clampQty(value) {
    var n = parseInt(value, 10);
    if (isNaN(n)) n = minQty;
    return Math.min(maxQty, Math.max(minQty, n));
  }

  function setQty(value, syncInput) {
    if (!qty) return minQty;
    var next = clampQty(value);
    if (syncInput !== false) qty.value = String(next);
    if (minusBtn) minusBtn.disabled = next <= minQty;
    if (plusBtn) plusBtn.disabled = next >= maxQty;
    syncLinks();
    return next;
  }

  function currentQty() {
    return qty ? clampQty(qty.value || minQty) : minQty;
  }

  function currentItem() {
    return {
      slug: cfg.slug,
      name: cfg.name,
      image: cfg.image,
      url: cfg.url,
      category: cfg.category,
      qty: currentQty(),
    };
  }

  function syncWish() {
    var bag = store();
    if (!wishBtn || !bag) return;
    var saved = bag.isWishlisted(cfg.slug);
    wishBtn.classList.toggle("is-active", saved);
    wishBtn.innerHTML = saved
      ? '<i class="fa-solid fa-heart"></i> Saved to Wishlist'
      : '<i class="fa-regular fa-heart"></i> Add to Wishlist';
  }

  function enquiryText() {
    return (
      "Hi, I would like a rental enquiry for " +
      cfg.name +
      " from the " +
      (cfg.category || "") +
      " collection (quantity: " +
      currentQty() +
      "). " +
      (cfg.url ? "Product: " + window.location.origin + cfg.url : "")
    );
  }

  function syncLinks() {
    if (!waBtn) return;
    waBtn.href =
      "https://wa.me/" +
      cfg.whatsapp +
      "?text=" +
      encodeURIComponent(enquiryText());
  }

  function addToCart() {
    var bag = store();
    if (!bag || !cartBtn) return;
    bag.addToCart(currentItem());
    if (typeof bag.updateCounts === "function") bag.updateCounts();
    cartBtn.innerHTML = '<i class="fa-solid fa-check"></i> Added to Cart';
    window.clearTimeout(cartResetTimer);
    cartResetTimer = window.setTimeout(function () {
      cartBtn.innerHTML = '<i class="fa-solid fa-bag-shopping"></i> Add to Cart';
    }, 1600);
  }

  function toggleWishlist() {
    var bag = store();
    if (!bag || !wishBtn) return;
    bag.toggleWishlist(currentItem());
    if (typeof bag.updateCounts === "function") bag.updateCounts();
    syncWish();
  }

  if (qty) {
    qty.addEventListener("input", function () {
      var raw = qty.value.replace(/[^\d]/g, "");
      if (raw !== qty.value) qty.value = raw;
      if (raw === "") {
        if (minusBtn) minusBtn.disabled = true;
        if (plusBtn) plusBtn.disabled = false;
        return;
      }
      setQty(raw, false);
    });
    qty.addEventListener("change", function () {
      setQty(qty.value);
    });
    qty.addEventListener("blur", function () {
      setQty(qty.value || minQty);
    });
  }

  if (minusBtn) {
    minusBtn.addEventListener("click", function () {
      setQty(currentQty() - 1);
    });
  }

  if (plusBtn) {
    plusBtn.addEventListener("click", function () {
      setQty(currentQty() + 1);
    });
  }

  if (cartBtn) {
    cartBtn.addEventListener("click", function (event) {
      event.preventDefault();
      addToCart();
    });
  }

  if (wishBtn) {
    wishBtn.addEventListener("click", function (event) {
      event.preventDefault();
      toggleWishlist();
    });
  }

  setQty(qty ? qty.value : minQty);
  syncWish();
  syncLinks();

  function openLightbox() {
    if (!lightbox) return;
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.hidden = true;
    document.body.style.overflow = "";
  }

  if (mainImg) mainImg.addEventListener("click", openLightbox);
  if (closeBtn) {
    closeBtn.addEventListener("click", function (event) {
      event.stopPropagation();
      closeLightbox();
    });
  }
  if (lightbox) lightbox.addEventListener("click", closeLightbox);
})();
