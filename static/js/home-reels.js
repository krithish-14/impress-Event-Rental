(function () {
  var section = document.querySelector("[data-home-reels]");
  var modal = document.getElementById("reelModal");
  if (!section || !modal) return;

  var scroller = section.querySelector("[data-reels-scroller]");
  var prevBtn = section.querySelector("[data-reels-prev]");
  var nextBtn = section.querySelector("[data-reels-next]");
  var openButtons = Array.prototype.slice.call(section.querySelectorAll("[data-reel-open]"));
  var slides = Array.prototype.slice.call(modal.querySelectorAll("[data-reel-slide]"));
  var previewVideos = Array.prototype.slice.call(section.querySelectorAll("[data-reel-preview]"));
  var carouselPrev = modal.querySelector("[data-reel-carousel-prev]");
  var carouselNext = modal.querySelector("[data-reel-carousel-next]");
  var currentIndex = 0;
  var soundOn = true;

  if (!slides.length) return;

  function likedKey(code) {
    return "er_reel_liked_" + code;
  }

  function isLiked(code) {
    try {
      return window.localStorage.getItem(likedKey(code)) === "1";
    } catch (err) {
      return false;
    }
  }

  function setLiked(code, liked) {
    try {
      if (liked) window.localStorage.setItem(likedKey(code), "1");
      else window.localStorage.removeItem(likedKey(code));
    } catch (err) {
      /* ignore */
    }
  }

  function pausePreviews() {
    previewVideos.forEach(function (preview) {
      preview.pause();
    });
  }

  function playPreview(preview) {
    if (!preview || !modal.hidden) return;
    preview.muted = true;
    var playPromise = preview.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(function () {});
    }
  }

  function resumeVisiblePreviews() {
    if (!modal.hidden) return;
    previewVideos.forEach(function (preview) {
      var rect = preview.getBoundingClientRect();
      var visible =
        rect.width > 0 &&
        rect.right > 0 &&
        rect.left < window.innerWidth &&
        rect.bottom > 0 &&
        rect.top < window.innerHeight;
      if (visible) playPreview(preview);
      else preview.pause();
    });
  }

  function stopAllSlides() {
    slides.forEach(function (slide) {
      var media = slide.querySelector("video");
      if (!media) return;
      media.pause();
      media.muted = true;
      media.removeAttribute("src");
      media.load();
    });
  }

  function syncActiveControls(slide) {
    if (!slide) return;
    var code = slide.getAttribute("data-reel-code") || "";
    var likeBtn = slide.querySelector("[data-reel-like]");
    var soundBtn = slide.querySelector("[data-reel-sound]");
    var liked = isLiked(code);

    if (likeBtn) {
      likeBtn.setAttribute("aria-pressed", liked ? "true" : "false");
      likeBtn.classList.toggle("is-liked", liked);
      var likeIcon = likeBtn.querySelector("i");
      if (likeIcon) {
        likeIcon.className = liked ? "fa-solid fa-heart" : "fa-regular fa-heart";
      }
    }

    if (soundBtn) {
      soundBtn.setAttribute("aria-pressed", soundOn ? "true" : "false");
      var soundIcon = soundBtn.querySelector("i");
      if (soundIcon) {
        soundIcon.className = soundOn ? "fa-solid fa-volume-high" : "fa-solid fa-volume-xmark";
      }
    }
  }

  function playActiveSlide() {
    var slide = slides[currentIndex];
    if (!slide) return;
    var media = slide.querySelector("video");
    var src = slide.getAttribute("data-reel-video") || "";
    var poster = slide.getAttribute("data-reel-poster") || "";
    if (!media || !src) return;

    if (poster) media.setAttribute("poster", poster);
    if (media.getAttribute("src") !== src) {
      media.src = src;
      media.load();
    }

    media.muted = !soundOn;
    syncActiveControls(slide);

    var playPromise = media.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(function () {
        soundOn = false;
        media.muted = true;
        syncActiveControls(slide);
        media.play().catch(function () {});
      });
    }
  }

  function renderCarousel() {
    var total = slides.length;
    var prevIndex = (currentIndex - 1 + total) % total;
    var nextIndex = (currentIndex + 1) % total;

    slides.forEach(function (slide, index) {
      var media = slide.querySelector("video");
      slide.classList.remove("is-active", "is-prev", "is-next", "is-far");

      if (index === currentIndex) {
        slide.classList.add("is-active");
      } else if (index === prevIndex && total > 1) {
        slide.classList.add("is-prev");
      } else if (index === nextIndex && total > 1) {
        slide.classList.add("is-next");
      } else {
        slide.classList.add("is-far");
        if (media) {
          media.pause();
          if (media.getAttribute("src")) {
            media.removeAttribute("src");
            media.load();
          }
        }
      }

      if (slide.classList.contains("is-prev") || slide.classList.contains("is-next")) {
        var sideSrc = slide.getAttribute("data-reel-video") || "";
        var sidePoster = slide.getAttribute("data-reel-poster") || "";
        if (media && sideSrc) {
          if (sidePoster) media.setAttribute("poster", sidePoster);
          if (media.getAttribute("src") !== sideSrc) {
            media.src = sideSrc;
            media.load();
          }
          media.muted = true;
          media.play().catch(function () {});
        }
      }
    });

    playActiveSlide();
  }

  function openReel(index) {
    currentIndex = Math.max(0, Math.min(index, slides.length - 1));
    soundOn = true;
    pausePreviews();
    modal.hidden = false;
    document.body.classList.add("reel-modal-open");
    renderCarousel();
  }

  function closeReel() {
    stopAllSlides();
    modal.hidden = true;
    document.body.classList.remove("reel-modal-open");
    resumeVisiblePreviews();
  }

  function go(delta) {
    if (!slides.length) return;
    currentIndex = (currentIndex + delta + slides.length) % slides.length;
    renderCarousel();
  }

  openButtons.forEach(function (btn, index) {
    btn.addEventListener("click", function () {
      var code = btn.getAttribute("data-reel-code") || "";
      var matched = slides.findIndex(function (slide) {
        return slide.getAttribute("data-reel-code") === code;
      });
      openReel(matched >= 0 ? matched : index);
    });
  });

  modal.querySelectorAll("[data-reel-close]").forEach(function (el) {
    el.addEventListener("click", closeReel);
  });

  if (carouselPrev) {
    carouselPrev.addEventListener("click", function (event) {
      event.stopPropagation();
      go(-1);
    });
  }
  if (carouselNext) {
    carouselNext.addEventListener("click", function (event) {
      event.stopPropagation();
      go(1);
    });
  }

  slides.forEach(function (slide) {
    var tap = slide.querySelector("[data-reel-tap]");
    var likeBtn = slide.querySelector("[data-reel-like]");
    var soundBtn = slide.querySelector("[data-reel-sound]");
    var media = slide.querySelector("video");

    if (tap) {
      tap.addEventListener("click", function (event) {
        event.stopPropagation();
        if (!slide.classList.contains("is-active") || !media) {
          var idx = Number(slide.getAttribute("data-reel-index") || 0);
          currentIndex = idx;
          renderCarousel();
          return;
        }
        if (media.paused) playActiveSlide();
        else media.pause();
      });
    }

    if (likeBtn) {
      likeBtn.addEventListener("click", function (event) {
        event.stopPropagation();
        var code = slide.getAttribute("data-reel-code") || "";
        if (!code) return;
        setLiked(code, !isLiked(code));
        syncActiveControls(slide);
      });
    }

    if (soundBtn) {
      soundBtn.addEventListener("click", function (event) {
        event.stopPropagation();
        soundOn = !soundOn;
        if (media) media.muted = !soundOn;
        syncActiveControls(slide);
        if (soundOn && media && media.paused) {
          media.play().catch(function () {});
        }
      });
    }

    // Clicking a side card focuses that reel.
    slide.addEventListener("click", function (event) {
      if (slide.classList.contains("is-active")) return;
      if (event.target.closest(".reel-modal-btn")) return;
      var idx = Number(slide.getAttribute("data-reel-index") || 0);
      currentIndex = idx;
      renderCarousel();
    });
  });

  document.addEventListener("keydown", function (event) {
    if (modal.hidden) return;
    if (event.key === "Escape") closeReel();
    if (event.key === "ArrowLeft") go(-1);
    if (event.key === "ArrowRight") go(1);
  });

  function scrollReels(dir) {
    if (!scroller) return;
    var card = scroller.querySelector(".home-reel-card");
    var styles = window.getComputedStyle(scroller);
    var gap = parseFloat(styles.columnGap || styles.gap) || 0;
    var cardWidth = card ? card.getBoundingClientRect().width : 0;
    var amount;
    if (window.innerWidth <= 768 && cardWidth) {
      // Mobile: advance by exactly 3 cards (one full page, no peek).
      amount = (cardWidth + gap) * 3;
      var maxScroll = Math.max(0, scroller.scrollWidth - scroller.clientWidth);
      var nextLeft = Math.min(maxScroll, Math.max(0, scroller.scrollLeft + dir * amount));
      // Snap to page boundaries.
      var page = Math.round(nextLeft / amount) * amount;
      scroller.scrollTo({ left: Math.min(maxScroll, Math.max(0, page)), behavior: "smooth" });
      return;
    }
    if (cardWidth) {
      amount = Math.max(cardWidth + gap, Math.floor(scroller.clientWidth * 0.7));
    } else {
      amount = Math.max(220, Math.floor(scroller.clientWidth * 0.7));
    }
    scroller.scrollBy({ left: dir * amount, behavior: "smooth" });
  }

  if (prevBtn) prevBtn.addEventListener("click", function () { scrollReels(-1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { scrollReels(1); });
  if (scroller) {
    scroller.addEventListener("scroll", function () {
      window.clearTimeout(scroller._reelScrollTimer);
      scroller._reelScrollTimer = window.setTimeout(resumeVisiblePreviews, 120);
    }, { passive: true });
  }

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && modal.hidden) playPreview(entry.target);
          else entry.target.pause();
        });
      },
      { root: scroller || null, threshold: 0.35 }
    );
    previewVideos.forEach(function (preview) {
      observer.observe(preview);
      playPreview(preview);
    });
  } else {
    previewVideos.forEach(playPreview);
  }
})();
