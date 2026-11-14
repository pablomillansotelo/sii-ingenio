(function () {
  const masPanel = document.getElementById("campus-mas-panel");
  const perfilPanel = document.getElementById("campus-perfil-panel");
  const perfilBtn = document.getElementById("campus-perfil-btn");
  const loader = document.getElementById("campus-loader");
  const html = document.documentElement;
  const PREF_KEY = "campus-ingenio-prefs";

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

  function aplicarPrefs(prefs) {
    if (!prefs) return;
    html.setAttribute("data-campus-tema", prefs.tema || "claro");
    html.setAttribute("data-campus-acento", prefs.acento || "rojo");
    html.setAttribute("data-campus-carga", prefs.animacion_carga ? "1" : "0");
    document.body.classList.remove("campus-tema-claro", "campus-tema-oscuro");
    document.body.classList.add("campus-tema-" + (prefs.tema || "claro"));
  }

  function prefsServidor() {
    return {
      tema: html.getAttribute("data-campus-tema") || "claro",
      acento: html.getAttribute("data-campus-acento") || "rojo",
      animacion_carga: html.getAttribute("data-campus-carga") === "1",
    };
  }

  try {
    const cache = JSON.parse(localStorage.getItem(PREF_KEY) || "null");
    if (cache && cache.tema) aplicarPrefs(cache);
  } catch (err) {
    /* ignore */
  }
  const servidor = prefsServidor();
  aplicarPrefs(servidor);
  try {
    localStorage.setItem(PREF_KEY, JSON.stringify(servidor));
  } catch (err) {
    /* ignore */
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

  const form = document.getElementById("campus-apariencia-form");
  if (form) {
    form.addEventListener("change", function () {
      const tema = (form.querySelector('input[name="tema"]:checked') || {}).value;
      const acento = (form.querySelector('input[name="acento"]:checked') || {}).value;
      const carga = form.querySelector('input[name="animacion_carga"]');
      aplicarPrefs({
        tema: tema || servidor.tema,
        acento: acento || servidor.acento,
        animacion_carga: carga ? carga.checked : servidor.animacion_carga,
      });
    });
  }

  function mostrarCarga() {
    if (html.getAttribute("data-campus-carga") !== "1" || !loader) return;
    loader.hidden = false;
  }

  document.querySelectorAll(".campus-shell a[href]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const href = link.getAttribute("href") || "";
      if (!href || href.charAt(0) === "#" || link.target === "_blank") return;
      mostrarCarga();
    });
  });
})();
