// Bozza del sito di advisory: navigazione adattiva e modulo dimostrativo.

// Popover nativo; il polyfill si carica solo se il browser non lo supporta.
if (!Object.hasOwn(HTMLElement.prototype, "popover")) {
  import("https://unpkg.com/@oddbird/popover-polyfill@0.7.3/dist/popover.min.js");
}

// La navigazione diventa in linea solo quando la riga intera ci sta davvero.
const header = document.querySelector(".site-header");
const inner = header?.querySelector(".header-inner");
const menu = document.getElementById("site-menu");

if (header && inner && menu && "ResizeObserver" in window) {
  let larghezzaMisurata = 0;

  const aperto = () => {
    try { return menu.matches(":popover-open"); }
    catch { return menu.classList.contains(":popover-open"); }
  };

  const disponi = () => {
    const larghezza = header.clientWidth;
    // Da chiuso si rimisura solo se l'intestazione si è allargata: evita lo sfarfallio.
    if (!header.classList.contains("is-wide") && larghezza <= larghezzaMisurata) return;
    larghezzaMisurata = larghezza;

    const eraAperto = aperto();
    header.classList.add("is-measuring", "is-wide");
    menu.removeAttribute("popover");

    if (inner.scrollWidth > inner.clientWidth) {
      header.classList.remove("is-wide");
      menu.setAttribute("popover", "auto");
      if (eraAperto) menu.showPopover();
    }
    requestAnimationFrame(() => header.classList.remove("is-measuring"));
  };

  const osservatore = new ResizeObserver(disponi);
  osservatore.observe(header);
  osservatore.observe(menu);
}

// Modulo di contatto: validazione nativa, nessun invio in bozza.
const modulo = document.querySelector("form.modulo");

if (modulo) {
  const esito = modulo.querySelector(".esito");

  modulo.addEventListener("invalid", (e) => e.target.setAttribute("aria-invalid", "true"), true);

  modulo.addEventListener("focusout", (e) => {
    const campo = e.target;
    if (campo.willValidate && campo.value !== "" && !campo.validity.valid) campo.setAttribute("aria-invalid", "true");
  });

  modulo.addEventListener("input", (e) => {
    if (e.target.validity?.valid) e.target.removeAttribute("aria-invalid");
  });

  modulo.addEventListener("submit", (e) => {
    e.preventDefault();
    if (modulo.elements.sito_web.value) return; // campo trappola compilato: probabile spam
    esito.textContent = "Modulo dimostrativo: in questa bozza il messaggio non viene inviato a nessuno. Nel sito definitivo arriverà per email, senza essere salvato sul server.";
  });
}
