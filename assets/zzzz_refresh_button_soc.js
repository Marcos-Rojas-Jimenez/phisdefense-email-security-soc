/* =========================================================
   PhisDefense SOC - Refresh Button
   Inserta botón de actualización sin tocar Python.
   ========================================================= */

(function () {
  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function currentTime() {
    const d = new Date();
    return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function createRefreshWidget() {
    if (document.getElementById("phis-refresh-widget")) return;

    const widget = document.createElement("div");
    widget.id = "phis-refresh-widget";
    widget.className = "phis-refresh-widget";

    widget.innerHTML = `
      <span class="phis-refresh-dot"></span>
      <button class="phis-refresh-button" type="button">↻ Actualizar</button>
      <span class="phis-refresh-time">Última carga: ${currentTime()}</span>
    `;

    document.body.appendChild(widget);

    const btn = widget.querySelector(".phis-refresh-button");
    btn.addEventListener("click", function () {
      btn.innerText = "↻ Actualizando...";
      setTimeout(function () {
        window.location.reload();
      }, 250);
    });
  }

  function init() {
    createRefreshWidget();
    setTimeout(createRefreshWidget, 500);
    setTimeout(createRefreshWidget, 1500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  const observer = new MutationObserver(function () {
    createRefreshWidget();
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
