// Flips data-bs-theme on <html> and persists the choice — see the anti-FOUC
// script in app.html's <head> for how a stored choice is applied on load.
document.addEventListener("click", function (e) {
  var btn = e.target.closest(".gth-theme-toggle");
  if (!btn) return;
  var root = document.documentElement;
  var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-bs-theme", next);
  localStorage.setItem("gth-theme-mode", next);
});
