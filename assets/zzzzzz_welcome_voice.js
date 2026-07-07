/* =========================================================
   PhisDefense SOC - Voz de bienvenida
   Dice "Welcome to PhisDefense SOC" al entrar o tras primera interacción.
   ========================================================= */

(function () {
  const MESSAGE = "Welcome to PhisDefense SOC. Command center online.";
  const STORAGE_KEY = "phisdefense_welcome_voice_timestamp";

  function canSpeak() {
    return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
  }

  function alreadySpokenRecently() {
    try {
      const last = parseInt(sessionStorage.getItem(STORAGE_KEY) || "0", 10);
      const now = Date.now();

      // Evita repetir la voz muchas veces si se refresca rápido.
      // Cambia 30000 por 0 si quieres que suene siempre en cada F5.
      return now - last < 30000;
    } catch (e) {
      return false;
    }
  }

  function markSpoken() {
    try {
      sessionStorage.setItem(STORAGE_KEY, String(Date.now()));
    } catch (e) {}
  }

  function speakWelcome() {
    if (!canSpeak()) return;
    if (alreadySpokenRecently()) return;

    try {
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(MESSAGE);
      utterance.lang = "en-US";
      utterance.rate = 0.92;
      utterance.pitch = 0.9;
      utterance.volume = 0.75;

      const voices = window.speechSynthesis.getVoices();

      if (voices && voices.length) {
        const preferred =
          voices.find(v => /Microsoft.*English/i.test(v.name)) ||
          voices.find(v => /Google.*English/i.test(v.name)) ||
          voices.find(v => /English|en-US|en_GB/i.test(v.lang)) ||
          voices[0];

        if (preferred) {
          utterance.voice = preferred;
        }
      }

      window.speechSynthesis.speak(utterance);
      markSpoken();
    } catch (e) {
      // Algunos navegadores bloquean sonido hasta interacción del usuario.
    }
  }

  function speakAfterInteractionOnce() {
    speakWelcome();

    window.removeEventListener("click", speakAfterInteractionOnce, true);
    window.removeEventListener("keydown", speakAfterInteractionOnce, true);
    window.removeEventListener("pointerdown", speakAfterInteractionOnce, true);
  }

  function init() {
    if (!canSpeak()) return;

    // Intento inicial. Puede funcionar si el navegador lo permite.
    setTimeout(speakWelcome, 800);

    // Garantía: si el navegador bloquea autoplay, hablará tras primera interacción.
    window.addEventListener("click", speakAfterInteractionOnce, true);
    window.addEventListener("keydown", speakAfterInteractionOnce, true);
    window.addEventListener("pointerdown", speakAfterInteractionOnce, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Algunas voces cargan tarde; reintento suave.
  if ("speechSynthesis" in window) {
    window.speechSynthesis.onvoiceschanged = function () {
      setTimeout(speakWelcome, 500);
    };
  }
})();
