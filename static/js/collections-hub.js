(function () {
  var page = document.body;
  var form = document.getElementById("chubFilterForm");
  var productSelect = document.getElementById("chubProductSelect");
  var mapNode = document.getElementById("chubBrandProducts");
  var grid = document.getElementById("product-grid");
  var gridBtns = document.querySelectorAll(".chub-grid-btn");
  var brandOptions = document.querySelectorAll(".chub-brand-option");
  var headingEl = document.getElementById("chubHeading");
  var countEl = document.getElementById("chubCount");
  var searchInput = document.getElementById("chubSearch");
  var filterOpen = document.getElementById("chubFilterOpen");
  var filterClose = document.getElementById("chubFilterClose");
  var filterBackdrop = document.getElementById("chubFilterBackdrop");
  var filterApply = document.getElementById("chubFilterApply");
  var filterReset = document.getElementById("chubFilterReset");
  var filterBadge = document.getElementById("chubFilterBadge");
  var chipsEl = document.getElementById("chubActiveChips");
  if (!form || !productSelect || !grid) return;

  var brandProducts = {};
  try {
    brandProducts = JSON.parse(mapNode ? mapNode.textContent : "{}") || {};
  } catch (e) {
    brandProducts = {};
  }

  var requestId = 0;
  var searchTimer = null;
  var mobileQuery = window.matchMedia("(max-width: 900px)");

  function isMobile() {
    return mobileQuery.matches;
  }

  function selectedBrand() {
    var checked = form.querySelector('input[name="brand"]:checked');
    return checked ? checked.value : "";
  }

  function selectedBrandLabel() {
    var active = form.querySelector(".chub-brand-option.is-active span");
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
    if (current && productSelect.value !== current) {
      productSelect.value = "";
    }
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

  function syncHearts() {
    var store = window.EventRentalStore;
    if (!store) return;
    grid.querySelectorAll(".card-wish-btn").forEach(function (button) {
      var saved = store.isWishlisted(button.getAttribute("data-slug"));
      button.classList.toggle("is-active", saved);
      var icon = button.querySelector("i");
      if (icon) icon.className = saved ? "fa-solid fa-heart" : "fa-regular fa-heart";
      button.setAttribute("aria-pressed", saved ? "true" : "false");
    });
  }

  function updateFilterUi() {
    var brand = selectedBrand();
    var product = productSelect.value;
    var count = (brand ? 1 : 0) + (product ? 1 : 0);
    if (filterBadge) {
      if (count) {
        filterBadge.hidden = false;
        filterBadge.textContent = String(count);
      } else {
        filterBadge.hidden = true;
      }
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
      brandChip.className = "chub-chip";
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
      productChip.className = "chub-chip";
      productChip.innerHTML = "<span></span><button type=\"button\" aria-label=\"Remove product filter\">×</button>";
      productChip.querySelector("span").textContent = selectedProductLabel() || product;
      productChip.querySelector("button").addEventListener("click", function () {
        productSelect.value = "";
        loadFilters(true);
      });
      chipsEl.appendChild(productChip);
    }
  }

  function applySearch() {
    var q = (searchInput ? searchInput.value : "").trim().toLowerCase();
    var cards = grid.querySelectorAll(".product-card");
    var visible = 0;
    cards.forEach(function (card) {
      var name = (card.getAttribute("data-name") || "").toLowerCase();
      var category = (card.getAttribute("data-category") || "").toLowerCase();
      var match = !q || name.indexOf(q) !== -1 || category.indexOf(q) !== -1;
      card.hidden = !match;
      card.classList.toggle("is-search-hidden", !match);
      if (match) visible += 1;
    });
    var empty = grid.querySelector(".chub-empty");
    if (empty) empty.hidden = cards.length > 0;
    if (countEl && q) {
      countEl.textContent = visible + " product" + (visible === 1 ? "" : "s");
    }
  }

  function setLoading(isLoading) {
    grid.classList.toggle("is-loading", isLoading);
    form.classList.toggle("is-busy", isLoading);
  }

  function setFilterOpen(open) {
    if (!page) return;
    page.classList.toggle("is-filter-open", open);
    if (filterOpen) filterOpen.setAttribute("aria-expanded", open ? "true" : "false");
    if (filterBackdrop) filterBackdrop.setAttribute("aria-hidden", open ? "false" : "true");
  }

  function loadFilters(closeSheet) {
    var id = ++requestId;
    var url = buildUrl({ partial: "1" });
    var publicUrl = buildUrl();
    setLoading(true);
    grid.classList.remove("is-ready");
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
        grid.innerHTML = data.html || "";
        if (headingEl) headingEl.textContent = data.heading || "Collections";
        if (countEl) countEl.textContent = data.count_label || "";
        if (searchInput) searchInput.value = "";
        syncHearts();
        applySearch();
        updateFilterUi();
        if (closeSheet) setFilterOpen(false);
        try {
          window.history.pushState({ collections: true }, "", publicUrl);
        } catch (e) {}
        requestAnimationFrame(function () {
          grid.classList.add("is-ready");
          setLoading(false);
        });
      })
      .catch(function () {
        if (id !== requestId) return;
        setLoading(false);
        grid.classList.add("is-ready");
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

  if (filterApply) {
    filterApply.addEventListener("click", function () {
      loadFilters(true);
    });
  }

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

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") setFilterOpen(false);
  });

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(function () {
        applySearch();
        if (!(searchInput.value || "").trim() && countEl) {
          var total = grid.querySelectorAll(".product-card").length;
          countEl.textContent = total + " product" + (total === 1 ? "" : "s");
        }
      }, 120);
    });
  }

  function normalizeGrid(cols) {
    var value = String(cols);
    if (isMobile()) {
      if (value === "3" || value === "4") value = "2";
      if (value !== "1" && value !== "2") value = "2";
      return value;
    }
    if (value === "1") value = "3";
    if (value !== "2" && value !== "3" && value !== "4") value = "3";
    return value;
  }

  function setGrid(cols) {
    var value = normalizeGrid(cols);
    grid.classList.remove("grid-cols-1", "grid-cols-2", "grid-cols-3", "grid-cols-4");
    grid.classList.add("grid-cols-" + value);
    gridBtns.forEach(function (btn) {
      var active = btn.getAttribute("data-grid") === value;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    try {
      localStorage.setItem("eventRentalCollectionGrid", value);
    } catch (e) {}
  }

  gridBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      setGrid(btn.getAttribute("data-grid"));
    });
  });

  function onViewportChange() {
    var saved = "3";
    try {
      saved = localStorage.getItem("eventRentalCollectionGrid") || (isMobile() ? "2" : "3");
    } catch (e) {}
    setGrid(saved);
  }

  if (mobileQuery.addEventListener) mobileQuery.addEventListener("change", onViewportChange);
  else if (mobileQuery.addListener) mobileQuery.addListener(onViewportChange);

  onViewportChange();
  fillProducts(selectedBrand(), productSelect.value);
  updateFilterUi();
  grid.classList.add("is-ready");
})();
