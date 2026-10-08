// Iscrizione a Euribor Weekly: manda il modulo a MailerLite senza lasciare la pagina.
document.querySelectorAll('form[data-nl]').forEach(function (f) {
  f.addEventListener('submit', async function (e) {
    e.preventDefault();
    var esito = f.querySelector('.nl__esito'), bottone = f.querySelector('button');
    bottone.disabled = true;
    try {
      var r = await fetch(f.action, { method: 'POST', body: new URLSearchParams(new FormData(f)) });
      if (!(await r.json()).success) throw new Error('rifiutata');
      f.querySelectorAll('label, button, .nl__nota').forEach(function (x) { x.hidden = true; });
      esito.textContent = 'Quasi fatto: ti è arrivata una email in inglese da Euribor Weekly, con oggetto «Confirmation email». Aprila e premi «Confirm your email».';
    } catch (err) {
      esito.textContent = 'Iscrizione non riuscita. Riprova fra poco, oppure scrivi a info@bacchin.app.';
      bottone.disabled = false;
    }
    esito.hidden = false;
  });
});
