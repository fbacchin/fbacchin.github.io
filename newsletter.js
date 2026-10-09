// Iscrizione a Euribor Weekly: manda il modulo a MailerLite senza lasciare la pagina.
// I messaggi seguono la lingua della pagina (<html lang>); la newsletter resta in italiano.
var NL_TESTI = {
  it: ['Quasi fatto: ti è arrivata una email in inglese da Euribor Weekly, con oggetto «Confirmation email». Aprila e premi «Confirm your email».',
       'Iscrizione non riuscita. Riprova fra poco, oppure scrivi a info@bacchin.app.'],
  en: ['Almost done: you have an email from Euribor Weekly with the subject “Confirmation email”. Open it and press “Confirm your email”.',
       'The sign-up didn’t go through. Try again in a moment, or write to info@bacchin.app.'],
  fr: ['C’est presque fait : vous avez reçu un e-mail en anglais d’Euribor Weekly, avec l’objet « Confirmation email ». Ouvrez-le et appuyez sur « Confirm your email ».',
       'L’inscription n’a pas abouti. Réessayez dans un instant, ou écrivez à info@bacchin.app.'],
  de: ['Fast geschafft: Du hast eine E-Mail auf Englisch von Euribor Weekly mit dem Betreff „Confirmation email“ bekommen. Öffne sie und tippe auf „Confirm your email“.',
       'Die Anmeldung hat nicht geklappt. Versuch es gleich noch einmal oder schreib an info@bacchin.app.'],
  es: ['Casi listo: te ha llegado un correo en inglés de Euribor Weekly con el asunto «Confirmation email». Ábrelo y pulsa «Confirm your email».',
       'No se ha podido completar la suscripción. Inténtalo de nuevo en un momento o escribe a info@bacchin.app.']
};
var NL_T = NL_TESTI[(document.documentElement.lang || 'it').slice(0, 2)] || NL_TESTI.it;
document.querySelectorAll('form[data-nl]').forEach(function (f) {
  f.addEventListener('submit', async function (e) {
    e.preventDefault();
    var esito = f.querySelector('.nl__esito'), bottone = f.querySelector('button');
    bottone.disabled = true;
    try {
      var r = await fetch(f.action, { method: 'POST', body: new URLSearchParams(new FormData(f)) });
      if (!(await r.json()).success) throw new Error('rifiutata');
      f.querySelectorAll('label, button, .nl__nota').forEach(function (x) { x.hidden = true; });
      esito.textContent = NL_T[0];
    } catch (err) {
      esito.textContent = NL_T[1];
      bottone.disabled = false;
    }
    esito.hidden = false;
  });
});
