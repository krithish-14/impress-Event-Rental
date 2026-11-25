(function () {
  var tabs = document.querySelectorAll(".auth-method-tab");
  var methodField = document.getElementById("loginMethod");
  var phoneGroup = document.getElementById("phoneGroup");
  var emailGroup = document.getElementById("emailGroup");
  var phoneInput = document.getElementById("phone");
  var emailInput = document.getElementById("email");
  if (!tabs.length || !methodField) return;

  function setMethod(method) {
    var email = method === "email";
    methodField.value = email ? "email" : "phone";
    tabs.forEach(function (tab) {
      tab.classList.toggle("is-active", tab.getAttribute("data-method") === methodField.value);
    });
    if (phoneGroup) phoneGroup.hidden = email;
    if (emailGroup) emailGroup.hidden = !email;
    if (phoneInput) phoneInput.required = !email;
    if (emailInput) emailInput.required = email;
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      setMethod(tab.getAttribute("data-method"));
    });
  });
})();
