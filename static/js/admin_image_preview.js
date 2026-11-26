(function () {
  function previewRoot() {
    return document.querySelector("[data-er-preview]");
  }

  function setPreview(src) {
    var root = previewRoot();
    if (!root) return;
    var img = root.querySelector("[data-er-preview-img]");
    var hint = root.querySelector("[data-er-preview-hint]");
    if (!img) return;

    if (src) {
      img.src = src;
      img.hidden = false;
      if (hint) hint.hidden = true;
    } else {
      img.removeAttribute("src");
      img.hidden = true;
      if (hint) hint.hidden = false;
    }
  }

  function bind() {
    var fileInput = document.getElementById("id_image");
    var urlInput = document.getElementById("id_image_url");
    if (!previewRoot()) return;

    if (fileInput) {
      fileInput.addEventListener("change", function () {
        var file = fileInput.files && fileInput.files[0];
        if (!file) {
          if (urlInput && urlInput.value.trim()) {
            setPreview(urlInput.value.trim());
          } else {
            setPreview("");
          }
          return;
        }
        if (!file.type || file.type.indexOf("image/") !== 0) {
          setPreview("");
          return;
        }
        var reader = new FileReader();
        reader.onload = function (event) {
          setPreview(event.target.result || "");
        };
        reader.readAsDataURL(file);
      });
    }

    if (urlInput) {
      var syncUrl = function () {
        if (fileInput && fileInput.files && fileInput.files[0]) return;
        setPreview(urlInput.value.trim());
      };
      urlInput.addEventListener("input", syncUrl);
      urlInput.addEventListener("change", syncUrl);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
