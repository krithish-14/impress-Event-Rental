(function () {
  var root = document.querySelector("[data-reviews-carousel]");
  if (!root) return;

  var track = root.querySelector("[data-reviews-track]");
  var dotsWrap = root.querySelector("[data-reviews-dots]");
  var prevBtn = root.querySelector("[data-reviews-prev]");
  var nextBtn = root.querySelector("[data-reviews-next]");
  var cards = Array.prototype.slice.call(track.querySelectorAll(".home-review-card"));
  if (!cards.length) return;

  var index = 0;
  var timer = null;

  function perView() {
    var width = window.innerWidth || document.documentElement.clientWidth;
    if (width <= 640) return 1;
    if (width <= 980) return 2;
    return 3;
  }

  function maxIndex() {
    return Math.max(0, cards.length - perView());
  }

  function buildDots() {
    if (!dotsWrap) return;
    dotsWrap.innerHTML = "";
    var pages = maxIndex() + 1;
    for (var i = 0; i < pages; i += 1) {
      var dot = document.createElement("button");
      dot.type = "button";
      dot.className = "home-reviews-dot" + (i === index ? " is-active" : "");
      dot.setAttribute("aria-label", "Go to reviews " + (i + 1));
      dot.setAttribute("data-reviews-dot", String(i));
      dotsWrap.appendChild(dot);
    }
  }

  function render() {
    var visible = perView();
    var capped = Math.min(index, maxIndex());
    index = capped;
    var gap = 18;
    var cardWidth = cards[0].getBoundingClientRect().width;
    var offset = capped * (cardWidth + gap);
    track.style.transform = "translateX(-" + offset + "px)";
    cards.forEach(function (card, i) {
      var active = i >= capped && i < capped + visible;
      card.classList.toggle("is-active", active);
    });
    if (dotsWrap) {
      var dots = dotsWrap.querySelectorAll(".home-reviews-dot");
      for (var d = 0; d < dots.length; d += 1) {
        dots[d].classList.toggle("is-active", d === capped);
      }
    }
  }

  function go(delta) {
    index += delta;
    if (index < 0) index = maxIndex();
    if (index > maxIndex()) index = 0;
    render();
    restart();
  }

  function restart() {
    if (timer) window.clearInterval(timer);
    timer = window.setInterval(function () {
      go(1);
    }, 5500);
  }

  if (prevBtn) prevBtn.addEventListener("click", function () { go(-1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { go(1); });
  if (dotsWrap) {
    dotsWrap.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-reviews-dot]");
      if (!btn) return;
      index = Number(btn.getAttribute("data-reviews-dot")) || 0;
      render();
      restart();
    });
  }

  var touchX = null;
  track.addEventListener(
    "touchstart",
    function (event) {
      touchX = event.changedTouches[0].clientX;
    },
    { passive: true }
  );
  track.addEventListener(
    "touchend",
    function (event) {
      if (touchX == null) return;
      var dx = event.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(dx) < 40) return;
      go(dx < 0 ? 1 : -1);
    },
    { passive: true }
  );

  window.addEventListener("resize", function () {
    buildDots();
    render();
  });

  buildDots();
  render();
  restart();
})();
