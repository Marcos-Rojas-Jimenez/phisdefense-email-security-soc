/* =========================================================
   PhisDefense SOC - Status Strip refinado
   Inserta barra de seguridad sin invadir el header.
   ========================================================= */

(function () {
  function createStrip() {
    if (document.getElementById("phis-status-strip")) return;

    const strip = document.createElement("div");
    strip.id = "phis-status-strip";
    strip.className = "phis-status-strip";

    strip.innerHTML = `
      <span class="phis-status-title">Security posture</span>
      <span class="phis-status-badge phis-status-ok">DMARC p=reject</span>
      <span class="phis-status-badge phis-status-ok">DKIM s2026</span>
      <span class="phis-status-badge phis-status-secure">SPF -all</span>
      <span class="phis-status-badge phis-status-purple">MTA-STS enforce</span>
      <span class="phis-status-badge phis-status-secure">TLS valid</span>
      <span class="phis-status-badge phis-status-block">Open Relay blocked</span>
      <span class="phis-status-badge phis-status-warn">TLS-RPT monitored</span>
    `;

    /*
      Inserción controlada:
      preferimos colocar la barra justo después del header/topbar,
      no arriba del todo.
    */
    const header =
      document.querySelector(".header") ||
      document.querySelector(".topbar") ||
      document.querySelector("[class*='header']") ||
      document.querySelector("[class*='topbar']");

    if (header && header.parentNode) {
      header.parentNode.insertBefore(strip, header.nextSibling);
      return;
    }

    const content =
      document.querySelector("#page-content") ||
      document.querySelector(".content") ||
      document.querySelector("main");

    if (content && content.parentNode) {
      content.parentNode.insertBefore(strip, content);
      return;
    }

    document.body.insertBefore(strip, document.body.firstChild);
  }

  function init() {
    createStrip();
    setTimeout(createStrip, 500);
    setTimeout(createStrip, 1500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  document.addEventListener("click", function () {
    setTimeout(createStrip, 300);
  }, true);
})();
