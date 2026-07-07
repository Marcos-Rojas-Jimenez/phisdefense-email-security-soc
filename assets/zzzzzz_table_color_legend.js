/* =========================================================
   PhisDefense SOC - Inserta leyenda encima de tablas
   ========================================================= */

(function () {
  function createLegend() {
    const tableShells = document.querySelectorAll(".table-shell");

    tableShells.forEach(function (shell, index) {
      if (shell.querySelector(".phis-table-legend")) return;

      const legend = document.createElement("div");
      legend.className = "phis-table-legend";
      legend.innerHTML = `
        <span class="phis-table-legend-title">Leyenda</span>

        <span class="phis-table-legend-item phis-legend-legit">
          <span class="phis-table-legend-dot"></span>
          Legítimo
        </span>

        <span class="phis-table-legend-item phis-legend-spoof">
          <span class="phis-table-legend-dot"></span>
          Spoofing / rechazo
        </span>

        <span class="phis-table-legend-item phis-legend-warning">
          <span class="phis-table-legend-dot"></span>
          Fallo controlado
        </span>

        <span class="phis-table-legend-item phis-legend-lookalike">
          <span class="phis-table-legend-dot"></span>
          Spam / lookalike
        </span>

        <span class="phis-table-legend-item phis-legend-soc">
          <span class="phis-table-legend-dot"></span>
          Pruebas SOC
        </span>

        <span class="phis-table-legend-item phis-legend-info">
          <span class="phis-table-legend-dot"></span>
          Informativo
        </span>
      `;

      const tableContainer = shell.querySelector(".dash-table-container");

      if (tableContainer) {
        shell.insertBefore(legend, tableContainer);
      } else {
        shell.appendChild(legend);
      }
    });
  }

  function init() {
    createLegend();
    setTimeout(createLegend, 500);
    setTimeout(createLegend, 1500);
    setTimeout(createLegend, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  const observer = new MutationObserver(function () {
    createLegend();
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
