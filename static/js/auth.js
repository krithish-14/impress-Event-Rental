document.querySelectorAll(".auth-toggle-password").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var input = document.getElementById(btn.getAttribute("data-target"));
    if (!input) return;
    var hidden = input.type === "password";
    input.type = hidden ? "text" : "password";
    var icon = btn.querySelector("i");
    if (icon) {
      icon.className = hidden ? "fa-regular fa-eye-slash" : "fa-regular fa-eye";
    }
    btn.setAttribute("aria-label", hidden ? "Hide password" : "Show password");
  });
});
