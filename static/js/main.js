(function () {
  var menuBtn = document.getElementById("mobileMenuBtn");
  var menu = document.getElementById("mobileMenu");
  var collectionsBtn = document.getElementById("mobileCollectionsBtn");
  var collections = document.getElementById("mobileCollections");

  if (menuBtn && menu) {
    menuBtn.addEventListener("click", function () {
      menu.classList.toggle("active");
    });
  }

  if (collectionsBtn && collections) {
    collectionsBtn.addEventListener("click", function () {
      var open = collections.classList.toggle("active");
      collectionsBtn.textContent = open ? "COLLECTIONS −" : "COLLECTIONS +";
    });
  }

  document.querySelectorAll(".dropdown-toggle").forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
    });
  });

  function closeAccountMenus(except) {
    document.querySelectorAll(".header-account.is-open").forEach(function (account) {
      if (account === except) return;
      account.classList.remove("is-open");
      var avatar = account.querySelector(".header-avatar");
      if (avatar) avatar.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", function (event) {
    var btn = event.target.closest(".header-avatar");
    var account = event.target.closest(".header-account");
    if (btn && account) {
      event.preventDefault();
      event.stopPropagation();
      var shouldOpen = !account.classList.contains("is-open");
      closeAccountMenus();
      if (shouldOpen) {
        account.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
      }
      return;
    }
    if (!account) closeAccountMenus();
  });

  var slider = document.getElementById("colSlider");
  if (slider) {
    var viewport = slider.querySelector(".col-slider-viewport");
    var track = slider.querySelector(".col-slider-track");
    var prevBtn = slider.querySelector(".col-slider-prev");
    var nextBtn = slider.querySelector(".col-slider-next");
    var dotsWrap = document.getElementById("colSliderDots");
    var originals = Array.prototype.slice.call(track.children);
    var total = originals.length;
    var index = 0;
    var timer = null;
    var hovering = false;

    function visibleCount() {
      if (window.innerWidth <= 600) return 1;
      if (window.innerWidth <= 900) return 2;
      return 3;
    }

    function gapSize() {
      var styles = window.getComputedStyle(track);
      return parseFloat(styles.columnGap || styles.gap) || 0;
    }

    function layout() {
      var visible = visibleCount();
      var gap = gapSize();
      var width = (viewport.clientWidth - gap * (visible - 1)) / visible;
      Array.prototype.forEach.call(track.children, function (card) {
        card.style.width = width + "px";
        card.style.flex = "0 0 " + width + "px";
      });
    }

    function stepSize() {
      var first = track.querySelector(".col-card");
      if (!first) return 0;
      return first.getBoundingClientRect().width + gapSize();
    }

    function maxIndex() {
      return Math.max(0, total - visibleCount());
    }

    function renderDots() {
      if (!dotsWrap) return;
      var pages = maxIndex() + 1;
      dotsWrap.innerHTML = "";
      for (var i = 0; i < pages; i += 1) {
        var dot = document.createElement("button");
        dot.type = "button";
        dot.className = "col-slider-dot" + (i === index ? " is-active" : "");
        dot.setAttribute("aria-label", "Go to collection set " + (i + 1));
        dot.addEventListener("click", function (pageIndex) {
          return function () {
            goTo(pageIndex, true);
          };
        }(i));
        dotsWrap.appendChild(dot);
      }
    }

    function goTo(next, userAction) {
      index = Math.max(0, Math.min(next, maxIndex()));
      track.classList.add("is-ready");
      track.style.transform = "translateX(" + (-index * stepSize()) + "px)";
      if (dotsWrap) {
        Array.prototype.forEach.call(dotsWrap.children, function (dot, i) {
          dot.classList.toggle("is-active", i === index);
        });
      }
      if (userAction) restart();
    }

    function next() {
      goTo(index >= maxIndex() ? 0 : index + 1, false);
    }

    function prev() {
      goTo(index <= 0 ? maxIndex() : index - 1, false);
    }

    function restart() {
      window.clearInterval(timer);
      timer = window.setInterval(function () {
        if (!hovering) next();
      }, 3800);
    }

    if (prevBtn) prevBtn.addEventListener("click", function () {
      prev();
      restart();
    });
    if (nextBtn) nextBtn.addEventListener("click", function () {
      next();
      restart();
    });

    slider.addEventListener("mouseenter", function () { hovering = true; });
    slider.addEventListener("mouseleave", function () { hovering = false; });

    window.addEventListener("resize", function () {
      layout();
      if (index > maxIndex()) index = maxIndex();
      track.classList.remove("is-ready");
      track.style.transform = "translateX(" + (-index * stepSize()) + "px)";
      renderDots();
    });

    layout();
    renderDots();
    goTo(0, false);
    restart();
  }
})();
