/* =========================================================
   PhisDefense SOC - Clasificación visual uniforme por fila
   ========================================================= */

(function () {
  function norm(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function clearRowClasses(row) {
    [
      "pd-row-legit",
      "pd-row-spoof",
      "pd-row-rejected",
      "pd-row-warning",
      "pd-row-lookalike",
      "pd-row-spam",
      "pd-row-soc",
      "pd-row-info"
    ].forEach(function (cls) {
      row.classList.remove(cls);
    });
  }

  function clearCellTextClasses(cell) {
    [
      "pd-text-pass",
      "pd-text-fail",
      "pd-text-none",
      "pd-text-warning",
      "pd-text-info"
    ].forEach(function (cls) {
      cell.classList.remove(cls);
    });
  }

  function getColumn(cell) {
    return (
      cell.getAttribute("data-dash-column") ||
      cell.getAttribute("data-column") ||
      ""
    );
  }

  function classifyRow(row) {
    const text = norm(row.innerText);

    if (text.includes("lookalike") || text.includes("phisdefence") || text.includes("typo")) {
      return "pd-row-lookalike";
    }

    if (text.includes("spoof")) {
      return "pd-row-spoof";
    }

    if (text.includes("rechazado") || text.includes("reject") || text.includes("relay access denied")) {
      return "pd-row-rejected";
    }

    if (text.includes("spam")) {
      return "pd-row-spam";
    }

    if (
      text.includes("dkim_fail") ||
      text.includes("spf_fail") ||
      text.includes("auth_fail") ||
      text.includes("recipient_unknown") ||
      text.includes("fallo")
    ) {
      return "pd-row-warning";
    }

    if (
      text.includes("smtp_auth") ||
      text.includes("dkim_rotation") ||
      text.includes("soc") ||
      text.includes("tls_ok")
    ) {
      return "pd-row-soc";
    }

    if (text.includes("legitimo") || text.includes("legit")) {
      return "pd-row-legit";
    }

    if (text.includes("maildir") || text.includes("enviado") || text.includes("sent")) {
      return "pd-row-info";
    }

    return "";
  }

  function classifyCellText(cell) {
    const col = norm(getColumn(cell));
    const val = norm(cell.innerText);

    clearCellTextClasses(cell);

    const authCols = ["spf", "dkim", "dmarc", "spf_result", "dkim_result", "dmarc_result"];
    const importantCols = [
      "resultado_esperado",
      "ubicacion_final",
      "clasificacion_real"
    ];

    if (!authCols.includes(col) && !importantCols.includes(col)) {
      return;
    }

    if (val === "pass" || val.includes("permitido") || val.includes("enviado")) {
      cell.classList.add("pd-text-pass");
      return;
    }

    if (val === "fail" || val.includes("rechaz") || val.includes("reject") || val.includes("spoof")) {
      cell.classList.add("pd-text-fail");
      return;
    }

    if (val === "none" || val === "no_aplica" || val === "n/a") {
      cell.classList.add("pd-text-none");
      return;
    }

    if (
      val.includes("fallo") ||
      val.includes("dkim") ||
      val.includes("spf") ||
      val.includes("auth") ||
      val.includes("recipient")
    ) {
      cell.classList.add("pd-text-warning");
      return;
    }

    if (val.includes("maildir") || val.includes("tls")) {
      cell.classList.add("pd-text-info");
      return;
    }
  }

  function applyRows() {
    document.querySelectorAll(".dash-table-container tbody tr").forEach(function (row) {
      const cells = row.querySelectorAll("td.dash-cell");
      if (!cells.length) return;

      clearRowClasses(row);

      const rowClass = classifyRow(row);
      if (rowClass) {
        row.classList.add(rowClass);
      }

      cells.forEach(classifyCellText);
    });
  }

  function removeTooltips() {
    document.querySelectorAll(
      ".dash-table-tooltip, .dash-tooltip, [class*='tooltip'], [class*='Tooltip']"
    ).forEach(function (el) {
      try { el.remove(); } catch (e) {}
    });

    document.querySelectorAll(
      ".dash-table-container [title], .dash-spreadsheet-container [title]"
    ).forEach(function (el) {
      el.removeAttribute("title");
      el.removeAttribute("aria-label");
      el.removeAttribute("data-title");
    });
  }

  function run() {
    applyRows();
    removeTooltips();
  }

  document.addEventListener("DOMContentLoaded", function () {
    run();
    setTimeout(run, 300);
    setTimeout(run, 900);
    setTimeout(run, 1800);
  });

  const observer = new MutationObserver(function () {
    clearTimeout(window.__pdUniformRowsTimeout);
    window.__pdUniformRowsTimeout = setTimeout(run, 100);
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  document.addEventListener("mouseover", function () {
    clearTimeout(window.__pdUniformRowsMouseTimeout);
    window.__pdUniformRowsMouseTimeout = setTimeout(run, 60);
  }, true);

  setInterval(run, 1500);
})();
