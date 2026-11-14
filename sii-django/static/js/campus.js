(function () {
  const masPanel = document.getElementById("campus-mas-panel");
  const perfilPanel = document.getElementById("campus-perfil-panel");
  const perfilBtn = document.getElementById("campus-perfil-btn");

  function abrir(panel, trigger) {
    if (!panel) return;
    panel.hidden = false;
    if (trigger) trigger.setAttribute("aria-expanded", "true");
  }

  function cerrar(panel, trigger) {
    if (!panel) return;
    panel.hidden = true;
    if (trigger) trigger.setAttribute("aria-expanded", "false");
  }

  document.querySelectorAll("[data-campus-mas-open]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      abrir(masPanel, btn);
    });
  });

  document.querySelectorAll("[data-campus-mas-close]").forEach(function (el) {
    el.addEventListener("click", function () {
      cerrar(masPanel);
    });
  });

  if (perfilBtn && perfilPanel) {
    perfilBtn.addEventListener("click", function () {
      if (perfilPanel.hidden) {
        abrir(perfilPanel, perfilBtn);
      } else {
        cerrar(perfilPanel, perfilBtn);
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    cerrar(masPanel);
    cerrar(perfilPanel, perfilBtn);
  });
})();
