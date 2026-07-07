/* =========================================================
   PhisDefense SOC - Clasificar KPI Entregabilidad
   Añade clases a tarjetas según etiqueta visible.
   ========================================================= */

(function () {
  function norm(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function classifyKpis() {
    document.querySelectorAll(".metric-card").forEach(function (card) {
      const label = norm(card.innerText);

      card.classList.remove(
        "kpi-deliverability-legit",
        "kpi-deliverability-smtp",
        "kpi-deliverability-inbox",
        "kpi-deliverability-spam",
        "kpi-deliverability-missing"
      );

      if (label.includes("legitimos gmail") || label.includes("legítimos gmail")) {
        card.classList.add("kpi-deliverability-legit");
        return;
      }

      if (label.includes("smtp aceptados")) {
        card.classList.add("kpi-deliverability-smtp");
        return;
      }

      if (label.includes("inbox")) {
        card.classList.add("kpi-deliverability-inbox");
        return;
      }

      if (label.includes("spam")) {
        card.classList.add("kpi-deliverability-spam");
        return;
      }

      if (label.includes("no aparece")) {
        card.classList.add("kpi-deliverability-missing");
        return;
      }
    });
  }

  function init() {
    classifyKpis();
    setTimeout(classifyKpis, 300);
    setTimeout(classifyKpis, 1000);
    setTimeout(classifyKpis, 2500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Reaplicar cuando se navega entre pestañas de Dash, sin observer agresivo.
  document.addEventListener("click", function () {
    setTimeout(classifyKpis, 350);
    setTimeout(classifyKpis, 900);
  }, true);
})();
