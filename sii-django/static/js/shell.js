(() => {
  const key = "ingenio.sidebar";
  const collapsed = localStorage.getItem(key) === "collapsed";
  if (collapsed) document.body.classList.add("shell-collapsed");

  const button = document.querySelector("[data-shell-toggle]");
  if (!button) return;
  const sync = () => {
    const isCollapsed = document.body.classList.contains("shell-collapsed");
    button.setAttribute("aria-expanded", String(!isCollapsed));
    button.setAttribute("title", isCollapsed ? "Mostrar menú" : "Ocultar menú");
  };
  sync();
  button.addEventListener("click", () => {
    document.body.classList.toggle("shell-collapsed");
    localStorage.setItem(
      key,
      document.body.classList.contains("shell-collapsed") ? "collapsed" : "expanded"
    );
    sync();
  });
})();
