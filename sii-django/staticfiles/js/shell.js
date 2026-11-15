(() => {
  const key = "ingenio.sidebar";
  const collapsed = localStorage.getItem(key) === "collapsed";
  if (collapsed) document.body.classList.add("shell-collapsed");

  const button = document.querySelector("[data-shell-toggle]");
  if (button) {
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
  }

  document.querySelectorAll("tr.table-row-link[data-href]").forEach((row) => {
    row.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, select, textarea, label")) return;
      const href = row.getAttribute("data-href");
      if (href) window.location.href = href;
    });
  });

  const applyTable = (table) => {
    const query = (table.dataset.search || "").trim().toLowerCase();
    const filter = table.dataset.filter || "";
    table.querySelectorAll("tbody tr").forEach((row) => {
      if (row.querySelector(".empty-state") || row.children.length === 1 && row.querySelector(".text-muted")) {
        return;
      }
      const text = row.innerText.toLowerCase();
      const matchesQuery = !query || text.includes(query);
      const matchesFilter = !filter || (row.getAttribute("data-filter") || "") === filter;
      row.hidden = !(matchesQuery && matchesFilter);
    });
  };

  document.querySelectorAll("[data-table-search]").forEach((input) => {
    const table = document.getElementById(input.getAttribute("data-table-search"));
    if (!table) return;
    input.addEventListener("input", () => {
      table.dataset.search = input.value;
      applyTable(table);
    });
  });

  const NAME_HEADERS = /nombre|alumno|cliente|curso|periodo|vendedor/i;

  document.querySelectorAll(".table-responsive table").forEach((table) => {
    table.classList.add("table-stack");
    const headers = Array.from(table.querySelectorAll("thead th")).map((th) =>
      th.textContent.replace(/\s+/g, " ").trim()
    );
    headers.forEach((label, index) => {
      if (NAME_HEADERS.test(label)) {
        table
          .querySelectorAll(`tr > :nth-child(${index + 1})`)
          .forEach((cell) => cell.classList.add("table-col-name"));
      }
      if (!label) {
        table
          .querySelectorAll(`tr > :nth-child(${index + 1})`)
          .forEach((cell) => cell.classList.add("table-col-actions"));
      }
    });
    table.querySelectorAll("tbody tr").forEach((row) => {
      Array.from(row.children).forEach((cell, index) => {
        if (cell.hasAttribute("colspan") || cell.querySelector(".empty-state")) return;
        if (!cell.getAttribute("data-label") && headers[index]) {
          cell.setAttribute("data-label", headers[index]);
        }
      });
    });
  });

  const activeTab = document.querySelector("[data-home-tabs] .nav-link.active");
  if (activeTab && typeof activeTab.scrollIntoView === "function") {
    activeTab.scrollIntoView({ inline: "center", block: "nearest", behavior: "auto" });
  }

  document.querySelectorAll("[data-table-filter]").forEach((group) => {
    const table = document.getElementById(group.getAttribute("data-table-filter"));
    if (!table) return;
    group.querySelectorAll("[data-value]").forEach((button) => {
      button.addEventListener("click", () => {
        group.querySelectorAll("[data-value]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        table.dataset.filter = button.getAttribute("data-value") || "";
        applyTable(table);
      });
    });
  });
})();
