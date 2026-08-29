(() => {
  "use strict";

  const sidebar = document.querySelector("#sidebar");
  const overlay = document.querySelector("#sidebar-overlay");
  const menuButton = document.querySelector("#menu-button");

  const closeMenu = () => document.body.classList.remove("menu-open");
  if (menuButton) menuButton.addEventListener("click", () => document.body.classList.toggle("menu-open"));
  if (overlay) overlay.addEventListener("click", closeMenu);
  if (sidebar) sidebar.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));

  document.querySelectorAll(".flash button").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash").remove());
  });

  window.setTimeout(() => {
    document.querySelectorAll(".flash.success").forEach((flash) => flash.classList.add("fade"));
  }, 4500);

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = button.parentElement.querySelector("input");
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      button.textContent = isPassword ? "Hide" : "Show";
      button.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
  });
})();
