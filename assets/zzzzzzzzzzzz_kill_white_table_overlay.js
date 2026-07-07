/* =========================================================
   PhisDefense SOC - Kill white overlays sin pisar colorines
   ========================================================= */

(function () {
  function rgbNums(value) {
    if (!value) return null;
    const m = String(value).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
    if (!m) return null;
    return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3])];
  }

  function isWhiteish(value) {
    const v = String(value || "").toLowerCase().replace(/\s+/g, "");
    if (
      v.includes("#fff") ||
      v.includes("#ffffff") ||
      v.includes("white") ||
      v.includes("rgb(255,255,255)") ||
      v.includes("rgba(255,255,255")
    ) return true;

    const nums = rgbNums(value);
    if (!nums) return false;

    const [r, g, b] = nums;
    return r >= 225 && g >= 225 && b >= 225;
  }

  function isInsideTable(el) {
    if (!el || !el.closest) return false;
    return (
      el.closest(".dash-table-container") ||
      el.closest(".dash-spreadsheet-container") ||
      el.closest(".table-shell")
    );
  }

  function darkenWhiteOverlay(el) {
    if (!el || !el.style) return;
    if (!isInsideTable(el)) return;

    // No tocar celdas coloreadas
    if (el.dataset && el.dataset.pdColorized === "true") return;
    if (el.closest && el.closest('[data-pd-colorized="true"]')) return;

    const tag = String(el.tagName || "").toLowerCase();
    if (tag === "svg" || tag === "path" || tag === "circle") return;

    const computed = window.getComputedStyle(el);
    const bg = computed.backgroundColor;
    const inlineBg = el.style.backgroundColor;

    if (isWhiteish(bg) || isWhiteish(inlineBg)) {
      el.style.setProperty("background", "#071426", "important");
      el.style.setProperty("background-color", "#071426", "important");
      el.style.setProperty("color", "#ecf6ff", "important");
      el.style.setProperty("box-shadow", "none", "important");
    }
  }

  function clean() {
    document.querySelectorAll(
      ".dash-table-tooltip, .dash-tooltip, [class*='tooltip'], [class*='Tooltip']"
    ).forEach(function (el) {
      try { el.remove(); } catch (e) {
        el.style.display = "none";
      }
    });

    document.querySelectorAll(
      ".dash-table-container [title], .dash-spreadsheet-container [title], .table-shell [title]"
    ).forEach(function (el) {
      el.removeAttribute("title");
      el.removeAttribute("aria-label");
      el.removeAttribute("data-title");
    });

    document.querySelectorAll(
      ".dash-table-container *, .dash-spreadsheet-container *, .table-shell *"
    ).forEach(function (el) {
      try { darkenWhiteOverlay(el); } catch (e) {}
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    clean();
    setTimeout(clean, 300);
    setTimeout(clean, 1000);
  });

  document.addEventListener("mousemove", function (event) {
    try {
      document.elementsFromPoint(event.clientX, event.clientY).forEach(darkenWhiteOverlay);
    } catch (e) {}
    clean();
  }, true);

  const observer = new MutationObserver(function () {
    clearTimeout(window.__pdOverlayTimeout);
    window.__pdOverlayTimeout = setTimeout(clean, 80);
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["style", "class", "title", "aria-label", "data-title"]
  });

  setInterval(clean, 1000);
})();
