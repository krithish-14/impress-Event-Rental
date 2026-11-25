(function () {
  var items = window.GALLERY_ITEMS || [];
  var queryInput = document.getElementById("galleryQuery");
  var section = document.getElementById("gallerySection");
  var results = document.getElementById("gallery-search-results");
  var countEl = document.getElementById("gallery-result-count");
  var emptyEl = document.getElementById("gallery-no-results");
  var categoriesWrap = document.getElementById("galleryCategories");
  var searchBox = document.getElementById("gallerySearchBox");
  var lightbox = document.getElementById("lightbox");
  var lightboxImg = document.getElementById("lightboxImg");
  var caption = document.getElementById("lightboxCaption");
  var counter = document.getElementById("lightboxCounter");
  var imgWrap = document.getElementById("lightboxImgWrap");
  var activeCat = "all";
  var lightboxIndex = null;
  var scale = 1;
  var pan = { x: 0, y: 0 };
  var drag = null;

  function filtered() {
    var words = (queryInput.value || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
    return items.filter(function (item) {
      var catMatch = activeCat === "all" || item.category === activeCat;
      var captionText = (item.name || "").toLowerCase();
      var textMatch = words.length === 0 || words.every(function (word) {
        return captionText.indexOf(word) !== -1;
      });
      return catMatch && textMatch;
    });
  }

  function render() {
    var query = (queryInput.value || "").trim();
    var searching = query.length > 0 || activeCat !== "all";
    section.classList.toggle("search-active", searching);
    searchBox.classList.toggle("has-value", query.length > 0);
    var matched = filtered();

    if (!searching) {
      results.innerHTML = "";
      countEl.textContent = "";
      emptyEl.style.display = "none";
      categoriesWrap.style.display = "";
      return;
    }

    categoriesWrap.style.display = "none";
    countEl.textContent = matched.length + " product" + (matched.length === 1 ? "" : "s") + " found";
    emptyEl.style.display = matched.length ? "none" : "flex";
    results.innerHTML = matched.map(function (item, i) {
      var origIndex = items.findIndex(function (g) {
        return g.img === item.img && g.name === item.name;
      });
      return (
        '<div class="product-card" data-open="' + origIndex + '">' +
          '<div class="product-card-img">' +
            '<span class="product-card-cat">' + item.categoryLabel + "</span>" +
            '<img src="' + item.img + '" alt="' + item.name + '" loading="lazy" />' +
            '<div class="product-card-view"><i class="fa-solid fa-magnifying-glass-plus"></i></div>' +
          "</div>" +
          '<div class="product-card-info">' +
            '<div class="product-card-name">' + item.name + "</div>" +
            '<div class="product-card-tag">' + item.categoryLabel + "</div>" +
          "</div>" +
        "</div>"
      );
    }).join("");
  }

  function resetZoom() {
    scale = 1;
    pan = { x: 0, y: 0 };
    applyTransform();
  }

  function applyTransform() {
    if (lightboxImg) {
      lightboxImg.style.transform = "translate(" + pan.x + "px, " + pan.y + "px) scale(" + scale + ")";
    }
  }

  function openLightbox(index) {
    if (index < 0 || index >= items.length) return;
    lightboxIndex = index;
    var item = items[index];
    lightboxImg.src = item.img;
    lightboxImg.alt = item.name;
    caption.textContent = item.name;
    counter.textContent = index + 1 + " / " + items.length;
    lightbox.classList.add("active");
    document.body.style.overflow = "hidden";
    resetZoom();
  }

  function closeLightbox() {
    lightbox.classList.remove("active");
    lightboxIndex = null;
    document.body.style.overflow = "";
    resetZoom();
  }

  function showPrev() {
    if (lightboxIndex === null) return;
    openLightbox((lightboxIndex - 1 + items.length) % items.length);
  }

  function showNext() {
    if (lightboxIndex === null) return;
    openLightbox((lightboxIndex + 1) % items.length);
  }

  document.querySelectorAll(".filter-pill").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".filter-pill").forEach(function (el) { el.classList.remove("active"); });
      btn.classList.add("active");
      activeCat = btn.getAttribute("data-cat");
      render();
    });
  });

  if (queryInput) queryInput.addEventListener("input", render);
  var clearBtn = document.getElementById("galleryClear");
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      queryInput.value = "";
      render();
      queryInput.focus();
    });
  }

  document.addEventListener("click", function (event) {
    var card = event.target.closest("[data-open]");
    if (card) {
      openLightbox(Number(card.getAttribute("data-open")));
      return;
    }
    var galleryItem = event.target.closest(".gallery-item");
    if (galleryItem) {
      var name = galleryItem.getAttribute("data-name");
      var img = galleryItem.getAttribute("data-img");
      var index = items.findIndex(function (item) {
        return item.name === name && item.img === img;
      });
      openLightbox(index);
    }
  });

  document.getElementById("lightboxBackdrop").addEventListener("click", closeLightbox);
  document.getElementById("lbClose").addEventListener("click", closeLightbox);
  document.getElementById("lbPrev").addEventListener("click", showPrev);
  document.getElementById("lbNext").addEventListener("click", showNext);
  document.getElementById("lbZoomIn").addEventListener("click", function () {
    scale = Math.min(scale + 0.3, 4);
    applyTransform();
  });
  document.getElementById("lbZoomOut").addEventListener("click", function () {
    scale = Math.max(scale - 0.3, 1);
    if (scale === 1) pan = { x: 0, y: 0 };
    applyTransform();
  });
  document.getElementById("lbReset").addEventListener("click", resetZoom);

  document.addEventListener("keydown", function (event) {
    if (lightboxIndex === null) return;
    if (event.key === "Escape") closeLightbox();
    if (event.key === "ArrowLeft") showPrev();
    if (event.key === "ArrowRight") showNext();
  });

  imgWrap.addEventListener("mousedown", function (event) {
    if (scale <= 1) return;
    drag = { startX: event.clientX, startY: event.clientY, panX: pan.x, panY: pan.y };
  });
  window.addEventListener("mousemove", function (event) {
    if (!drag) return;
    pan = { x: drag.panX + (event.clientX - drag.startX), y: drag.panY + (event.clientY - drag.startY) };
    applyTransform();
  });
  window.addEventListener("mouseup", function () { drag = null; });

  render();
})();
