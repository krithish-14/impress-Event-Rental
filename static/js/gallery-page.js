(function () {
  var section = document.getElementById("gallerySection");
  if (!section) return;

  var filters = Array.prototype.slice.call(
    section.querySelectorAll("[data-gallery-filter]")
  );
  var groups = Array.prototype.slice.call(
    section.querySelectorAll("[data-gallery-group]")
  );
  var items = Array.prototype.slice.call(
    section.querySelectorAll("[data-gallery-item]")
  );
  var lightbox = document.getElementById("galleryLightbox");
  var lightboxImg = document.getElementById("galleryLightboxImg");
  var lightboxCaption = document.getElementById("galleryLightboxCaption");
  var closeBtn = document.getElementById("galleryLightboxClose");
  var prevBtn = document.getElementById("galleryLightboxPrev");
  var nextBtn = document.getElementById("galleryLightboxNext");
  var activeIndex = -1;
  var visibleItems = items.slice();

  function setFilter(slug) {
    filters.forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-gallery-filter") === slug);
    });
    groups.forEach(function (group) {
      var match = slug === "all" || group.getAttribute("data-gallery-group") === slug;
      group.classList.toggle("is-hidden", !match);
    });
    visibleItems = items.filter(function (item) {
      var group = item.closest("[data-gallery-group]");
      return group && !group.classList.contains("is-hidden");
    });
  }

  function openLightbox(index) {
    if (!lightbox || !visibleItems.length) return;
    activeIndex = (index + visibleItems.length) % visibleItems.length;
    var item = visibleItems[activeIndex];
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

  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      setFilter(btn.getAttribute("data-gallery-filter") || "all");
    });
  });

  items.forEach(function (item, index) {
    item.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      visibleItems = items.filter(function (entry) {
        var group = entry.closest("[data-gallery-group]");
        return group && !group.classList.contains("is-hidden");
      });
      var nextIndex = visibleItems.indexOf(item);
      openLightbox(nextIndex >= 0 ? nextIndex : index);
    });
  });

  if (closeBtn) closeBtn.addEventListener("click", closeLightbox);
  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      openLightbox(activeIndex - 1);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      openLightbox(activeIndex + 1);
    });
  }

  if (lightbox) {
    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox) closeLightbox();
    });
  }

  document.addEventListener("keydown", function (event) {
    if (lightbox && !lightbox.hidden) {
      if (event.key === "Escape") closeLightbox();
      if (event.key === "ArrowLeft") openLightbox(activeIndex - 1);
      if (event.key === "ArrowRight") openLightbox(activeIndex + 1);
    }
  });

  setFilter("all");
})();
