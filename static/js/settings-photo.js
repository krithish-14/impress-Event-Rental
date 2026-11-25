(function () {
  var viewSize = 280;
  var OUT = 512;
  var input = document.getElementById("settingsPhotoInput");
  var wrap = document.getElementById("settingsPhotoWrap");
  var preview = document.getElementById("settingsPhotoPreview");
  var icon = document.getElementById("settingsPhotoIcon");
  var adjustBtn = document.getElementById("settingsPhotoAdjust");
  var modal = document.getElementById("photoCropModal");
  var viewport = document.getElementById("photoCropViewport");
  var cropImg = document.getElementById("photoCropImage");
  var zoom = document.getElementById("photoCropZoom");
  var applyBtn = document.getElementById("photoCropApply");

  if (!input || !wrap || !preview || !modal || !viewport || !cropImg || !zoom || !applyBtn) return;

  var minScale = 1;
  var scale = 1;
  var x = 0;
  var y = 0;
  var dragging = false;
  var lastX = 0;
  var lastY = 0;
  var objectUrl = "";
  var openedFromFile = false;

  function showPhoto(src) {
    preview.src = src;
    preview.classList.remove("is-hidden");
    wrap.classList.add("has-photo");
    if (icon) icon.classList.add("is-hidden");
    if (adjustBtn) adjustBtn.hidden = false;
  }

  function setTransform() {
    var w = cropImg.naturalWidth * scale;
    var h = cropImg.naturalHeight * scale;
    x = Math.min(0, Math.max(viewSize - w, x));
    y = Math.min(0, Math.max(viewSize - h, y));
    cropImg.style.width = w + "px";
    cropImg.style.height = h + "px";
    cropImg.style.left = x + "px";
    cropImg.style.top = y + "px";
  }

  function setZoomFromScale() {
    zoom.value = String(scale / minScale);
  }

  function fitImage() {
    var nw = cropImg.naturalWidth;
    var nh = cropImg.naturalHeight;
    if (!nw || !nh) return;
    viewSize = viewport.clientWidth || 280;
    minScale = Math.max(viewSize / nw, viewSize / nh);
    scale = minScale * 1.08;
    x = (viewSize - nw * scale) / 2;
    y = (viewSize - nh * scale) / 2;
    zoom.min = "1";
    zoom.max = "3";
    setZoomFromScale();
    setTransform();
  }

  function openModal() {
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = "";
    }
  }

  function loadIntoCropper(src) {
    openModal();
    function ready() {
      requestAnimationFrame(fitImage);
    }
    cropImg.onload = ready;
    if (cropImg.src === src && cropImg.complete && cropImg.naturalWidth) {
      ready();
      return;
    }
    cropImg.src = src;
  }

  function assignFile(file) {
    if (typeof DataTransfer === "undefined") return;
    var data = new DataTransfer();
    data.items.add(file);
    input.files = data.files;
  }

  input.addEventListener("change", function () {
    var file = input.files && input.files[0];
    if (!file) return;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    openedFromFile = true;
    loadIntoCropper(objectUrl);
  });

  if (adjustBtn) {
    adjustBtn.addEventListener("click", function () {
      if (!preview.src || preview.classList.contains("is-hidden")) return;
      openedFromFile = false;
      loadIntoCropper(preview.src);
    });
  }

  wrap.addEventListener("click", function () {
    if (wrap.classList.contains("has-photo") && preview.src && !preview.classList.contains("is-hidden")) {
      openedFromFile = false;
      loadIntoCropper(preview.src);
    } else {
      input.click();
    }
  });

  zoom.addEventListener("input", function () {
    var next = minScale * Number(zoom.value);
    var cx = (viewSize / 2 - x) / scale;
    var cy = (viewSize / 2 - y) / scale;
    scale = next;
    x = viewSize / 2 - cx * scale;
    y = viewSize / 2 - cy * scale;
    setTransform();
  });

  viewport.addEventListener("wheel", function (event) {
    event.preventDefault();
    var factor = event.deltaY < 0 ? 1.06 : 0.94;
    var next = Math.min(minScale * 3, Math.max(minScale, scale * factor));
    var cx = (viewSize / 2 - x) / scale;
    var cy = (viewSize / 2 - y) / scale;
    scale = next;
    x = viewSize / 2 - cx * scale;
    y = viewSize / 2 - cy * scale;
    setZoomFromScale();
    setTransform();
  }, { passive: false });

  viewport.addEventListener("pointerdown", function (event) {
    dragging = true;
    lastX = event.clientX;
    lastY = event.clientY;
    viewport.classList.add("is-dragging");
    viewport.setPointerCapture(event.pointerId);
  });

  viewport.addEventListener("pointermove", function (event) {
    if (!dragging) return;
    x += event.clientX - lastX;
    y += event.clientY - lastY;
    lastX = event.clientX;
    lastY = event.clientY;
    setTransform();
  });

  function stopDrag(event) {
    dragging = false;
    viewport.classList.remove("is-dragging");
    if (event && viewport.hasPointerCapture(event.pointerId)) {
      viewport.releasePointerCapture(event.pointerId);
    }
  }

  viewport.addEventListener("pointerup", stopDrag);
  viewport.addEventListener("pointercancel", stopDrag);

  applyBtn.addEventListener("click", function () {
    var canvas = document.createElement("canvas");
    canvas.width = OUT;
    canvas.height = OUT;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;
    var ratio = OUT / viewSize;
    ctx.fillStyle = "#f8f6f1";
    ctx.fillRect(0, 0, OUT, OUT);
    ctx.drawImage(
      cropImg,
      x * ratio,
      y * ratio,
      cropImg.naturalWidth * scale * ratio,
      cropImg.naturalHeight * scale * ratio
    );
    canvas.toBlob(function (blob) {
      if (!blob) return;
      var file = new File([blob], "avatar.jpg", { type: "image/jpeg" });
      assignFile(file);
      openedFromFile = false;
      showPhoto(URL.createObjectURL(blob));
      closeModal();
    }, "image/jpeg", 0.92);
  });

  modal.querySelectorAll("[data-crop-close]").forEach(function (el) {
    el.addEventListener("click", function () {
      closeModal();
      if (openedFromFile) {
        input.value = "";
        openedFromFile = false;
      }
    });
  });
})();
