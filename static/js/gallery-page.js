(function () {
  var page = document.body;
  var section = document.getElementById("gallerySection");
  var form = document.getElementById("galleryFilterForm");
  var productSelect = document.getElementById("galleryProductSelect");
  var mapNode = document.getElementById("galleryBrandProducts");
  var results = document.getElementById("galleryResults");
  var brandOptions = document.querySelectorAll(".gallery-brand-option");
  var headingEl = document.getElementById("galleryHeading");
  var countEl = document.getElementById("galleryCount");
  var searchInput = document.getElementById("gallerySearch");
  var shopLink = document.getElementById("galleryShopLink");
  var filterOpen = document.getElementById("galleryFilterOpen");
  var filterClose = document.getElementById("galleryFilterClose");
  var filterBackdrop = document.getElementById("galleryFilterBackdrop");
  var filterApply = document.getElementById("galleryFilterApply");
  var filterReset = document.getElementById("galleryFilterReset");
  var filterBadge = document.getElementById("galleryFilterBadge");
  var chipsEl = document.getElementById("galleryActiveChips");
  if (!section || !form || !productSelect || !results) return;

  var brandProducts = {};
  try {
    brandProducts = JSON.parse(mapNode ? mapNode.textContent : "{}") || {};
  } catch (e) {
    brandProducts = {};
  }

  var requestId = 0;
  var searchTimer = null;
  var mobileQuery = window.matchMedia("(max-width: 900px)");
  var lightbox = document.getElementById("galleryLightbox");
  var lightboxImg = document.getElementById("galleryLightboxImg");
  var lightboxCaption = document.getElementById("galleryLightboxCaption");
  var closeBtn = document.getElementById("galleryLightboxClose");
  var prevBtn = document.getElementById("galleryLightboxPrev");
  var nextBtn = document.getElementById("galleryLightboxNext");
  var activeIndex = -1;
  var visibleItems = [];

  function isMobile() {
    return mobileQuery.matches;
  }

  function selectedBrand() {
    var checked = form.querySelector('input[name="brand"]:checked');
    return checked ? checked.value : "";
  }

  function selectedBrandLabel() {
    var active = form.querySelector(".gallery-brand-option.is-active span");
    return active ? active.textContent.trim() : "";
  }

  function selectedProductLabel() {
    var opt = productSelect.options[productSelect.selectedIndex];
    return opt && opt.value ? opt.textContent.trim() : "";
  }

  function fillProducts(brand, keepSlug) {
    var items = brandProducts[brand] || brandProducts[""] || [];
    var current = keepSlug || "";
    productSelect.innerHTML = "";
    var all = document.createElement("option");
    all.value = "";
    all.textContent = "All products";
    productSelect.appendChild(all);
    items.forEach(function (item) {
      var opt = document.createElement("option");
      opt.value = item.slug;
      opt.textContent = item.label;
      opt.setAttribute("data-brand", item.brand || "");
      if (item.slug === current) opt.selected = true;
      productSelect.appendChild(opt);
    });
    if (current && productSelect.value !== current) productSelect.value = "";
  }

  function buildUrl(extra) {
    var params = new URLSearchParams();
    var brand = selectedBrand();
    var product = productSelect.value;
    if (brand) params.set("brand", brand);
    if (product) params.set("product", product);
    if (extra) {
      Object.keys(extra).forEach(function (key) {
        if (extra[key] != null && extra[key] !== "") params.set(key, extra[key]);
      });
    }
    var query = params.toString();
    return form.getAttribute("action") + (query ? "?" + query : "");
  }

  function updateFilterUi() {
    var brand = selectedBrand();
    var product = productSelect.value;
    var count = (brand ? 1 : 0) + (product ? 1 : 0);
    if (filterBadge) {
      filterBadge.hidden = !count;
      filterBadge.textContent = String(count);
    }
    if (!chipsEl) return;
    chipsEl.innerHTML = "";
    if (!count) {
      chipsEl.hidden = true;
      return;
    }
    chipsEl.hidden = false;
    if (brand) {
      var brandChip = document.createElement("span");
      brandChip.className = "gallery-chip";
      brandChip.innerHTML = "<span></span><button type=\"button\" aria-label=\"Remove brand filter\">×</button>";
      brandChip.querySelector("span").textContent = selectedBrandLabel() || brand;
      brandChip.querySelector("button").addEventListener("click", function () {
        var allBrand = form.querySelector('input[name="brand"][value=""]');
        if (allBrand) {
          allBrand.checked = true;
          brandOptions.forEach(function (el) {
            el.classList.toggle("is-active", el.contains(allBrand));
          });
          fillProducts("", "");
          loadFilters(true);
        }
      });
      chipsEl.appendChild(brandChip);
    }
    if (product) {
      var productChip = document.createElement("span");
      productChip.className = "gallery-chip";
      productChip.innerHTML = "<span></span><button type=\"button\" aria-label=\"Remove product filter\">×</button>";
      productChip.querySelector("span").textContent = selectedProductLabel() || product;
      productChip.querySelector("button").addEventListener("click", function () {
        productSelect.value = "";
        loadFilters(true);
      });
      chipsEl.appendChild(productChip);
    }
  }

  function bindLightboxItems() {
    Array.prototype.forEach.call(results.querySelectorAll("[data-gallery-item]"), function (item) {
      item.addEventListener("click", function (event) {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        var items = getVisibleItems();
        var index = items.indexOf(item);
        openLightbox(index >= 0 ? index : 0);
      });
    });
  }

  function getVisibleItems() {
    return Array.prototype.slice.call(results.querySelectorAll("[data-gallery-item]")).filter(function (item) {
      return !item.classList.contains("is-search-hidden") && !item.hidden;
    });
  }

  function openLightbox(index) {
    var items = getVisibleItems();
    if (!lightbox || !items.length) return;
    visibleItems = items;
    activeIndex = (index + items.length) % items.length;
    var item = items[activeIndex];
    lightboxImg.src = item.getAttribute("data-image");
    lightboxImg.alt = item.getAttribute("data-name") || "";
    lightboxCaption.textContent =
      (item.getAttribute("data-name") || "") +
      " — " +
      (item.getAttribute("data-category") || "");
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.hidden = true;
    activeIndex = -1;
    document.body.style.overflow = "";
  }

  function applySearch() {
    var q = (searchInput ? searchInput.value : "").trim().toLowerCase();
    var tiles = results.querySelectorAll("[data-gallery-item]");
    var visible = 0;
    tiles.forEach(function (tile) {
      var name = (tile.getAttribute("data-name") || "").toLowerCase();
      var category = (tile.getAttribute("data-category") || "").toLowerCase();
      var match = !q || name.indexOf(q) !== -1 || category.indexOf(q) !== -1;
      tile.classList.toggle("is-search-hidden", !match);
      if (match) visible += 1;
    });
    results.querySelectorAll(".gallery-group").forEach(function (group) {
      var any = group.querySelectorAll("[data-gallery-item]:not(.is-search-hidden)").length > 0;
      group.classList.toggle("is-search-hidden", !any);
    });
    if (countEl && q) {
      countEl.textContent = visible + " item" + (visible === 1 ? "" : "s");
    }
  }

  function setLoading(isLoading) {
    results.classList.toggle("is-loading", isLoading);
    form.classList.toggle("is-busy", isLoading);
  }

  function setFilterOpen(open) {
    page.classList.toggle("is-filter-open", open);
    if (filterOpen) filterOpen.setAttribute("aria-expanded", open ? "true" : "false");
    if (filterBackdrop) filterBackdrop.setAttribute("aria-hidden", open ? "false" : "true");
  }

  function loadFilters(closeSheet) {
    var id = ++requestId;
    var url = buildUrl({ partial: "1" });
    var publicUrl = buildUrl();
    setLoading(true);
    results.classList.remove("is-ready");
    updateFilterUi();

    fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json",
      },
    })
      .then(function (res) {
        if (!res.ok) throw new Error("Filter request failed");
        return res.json();
      })
      .then(function (data) {
        if (id !== requestId) return;
        results.innerHTML = data.html || "";
        if (headingEl) headingEl.textContent = data.heading || "Gallery";
        if (countEl) countEl.textContent = data.count_label || "";
        if (shopLink) {
          if (data.shop_url) {
            shopLink.hidden = false;
            shopLink.href = data.shop_url;
            shopLink.textContent = data.shop_label || "View";
          } else {
            shopLink.hidden = true;
            shopLink.removeAttribute("href");
          }
        }
        if (searchInput) searchInput.value = "";
        bindLightboxItems();
        applySearch();
        updateFilterUi();
        if (closeSheet) setFilterOpen(false);
        try {
          window.history.pushState({ gallery: true }, "", publicUrl);
        } catch (e) {}
        requestAnimationFrame(function () {
          results.classList.add("is-ready");
          setLoading(false);
        });
      })
      .catch(function () {
        if (id !== requestId) return;
        setLoading(false);
        results.classList.add("is-ready");
        window.location.href = publicUrl;
      });
  }

  brandOptions.forEach(function (label) {
    var input = label.querySelector('input[name="brand"]');
    if (!input) return;
    input.addEventListener("change", function () {
      brandOptions.forEach(function (el) {
        el.classList.toggle("is-active", el.contains(input) && input.checked);
      });
      fillProducts(input.value, "");
      if (!isMobile()) loadFilters(false);
      else updateFilterUi();
    });
  });

  productSelect.addEventListener("change", function () {
    if (!isMobile()) loadFilters(false);
    else updateFilterUi();
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    loadFilters(true);
  });

  if (filterApply) filterApply.addEventListener("click", function () { loadFilters(true); });
  if (filterReset) {
    filterReset.addEventListener("click", function () {
      var allBrand = form.querySelector('input[name="brand"][value=""]');
      if (allBrand) allBrand.checked = true;
      brandOptions.forEach(function (el) {
        var input = el.querySelector('input[name="brand"]');
        el.classList.toggle("is-active", !!(input && input.value === ""));
      });
      fillProducts("", "");
      productSelect.value = "";
      loadFilters(true);
    });
  }

  if (filterOpen) filterOpen.addEventListener("click", function () { setFilterOpen(true); });
  if (filterClose) filterClose.addEventListener("click", function () { setFilterOpen(false); });
  if (filterBackdrop) filterBackdrop.addEventListener("click", function () { setFilterOpen(false); });

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(function () {
        applySearch();
        if (!(searchInput.value || "").trim() && countEl) {
          var total = results.querySelectorAll("[data-gallery-item]").length;
          countEl.textContent = total + " item" + (total === 1 ? "" : "s");
        }
      }, 120);
    });
  }

  if (closeBtn) closeBtn.addEventListener("click", closeLightbox);
  if (prevBtn) prevBtn.addEventListener("click", function () { openLightbox(activeIndex - 1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { openLightbox(activeIndex + 1); });
  if (lightbox) {
    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox) closeLightbox();
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      if (lightbox && !lightbox.hidden) closeLightbox();
      else setFilterOpen(false);
    }
    if (lightbox && !lightbox.hidden) {
      if (event.key === "ArrowLeft") openLightbox(activeIndex - 1);
      if (event.key === "ArrowRight") openLightbox(activeIndex + 1);
    }
  });

  fillProducts(selectedBrand(), productSelect.value);
  updateFilterUi();
  bindLightboxItems();
  results.classList.add("is-ready");
})();
