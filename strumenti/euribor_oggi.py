#!/usr/bin/env python3
"""Genera la pagina «Euribor oggi» in cinque lingue e aggiorna sitemap.xml.

Pagine: finanza/euribor-oggi.html (italiano), euribor-today (inglese),
euribor-aujourdhui (francese), euribor-heute (tedesco), euribor-hoy (spagnolo).
Si collegano fra loro con hreflang e con il selettore di lingua.

Legge i CSV pubblici di https://fbacchin.github.io/app/Euribor/ (EURIBOR.csv ed
ESTER.csv, le stesse serie usate dall'app Euribor X), calcola variazioni e
lettura della curva e scrive le pagine con i valori già dentro, così Google li
vede senza JavaScript.

Gira ogni giorno lavorativo da .github/workflows/euribor-oggi.yml. Se il fixing
non è cambiato, le pagine risultano identiche e il workflow non committa niente.
Solo libreria standard: nessuna dipendenza da installare.
"""
import csv, html, io, json, math, os, re, urllib.request
from datetime import date, timedelta

BASE = "https://fbacchin.github.io/app/Euribor/"
QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(QUI, "sitemap.xml")
SITO = "https://bacchin.app"
CSS_V = "2026-10-06c"
APP_ID = "951735963"
DASHBOARD = "/finanza/dashboard-bce"
NBSP, NNBSP = " ", " "

# Modulo di iscrizione alla newsletter: solo nella pagina italiana.
# Dopo ogni modifica a newsletter.css o newsletter.js, cambiare ?v= qui e in index.html.
NEWSLETTER_IT = '''    <section class="nl" id="newsletter">
      <link rel="stylesheet" href="/newsletter.css?v=2026-10-08b">
      <h2>Euribor Weekly</h2>
      <p>Ogni lunedì mattina, una email: i tassi Euribor della settimana, di quanto si sono mossi e cosa cambia per la rata di un mutuo variabile. Gratis. Il primo numero esce lunedì 19 ottobre 2026.</p>
      <form class="nl__form" data-nl method="post" action="https://assets.mailerlite.com/jsonp/2696788/forms/200787943386776821/subscribe">
      <label>Nome <input name="fields[name]" autocomplete="given-name" required></label>
      <label>Cognome <input name="fields[last_name]" autocomplete="family-name" required></label>
      <label class="larga">Email <input type="email" name="fields[email]" autocomplete="email" required></label>
      <input type="hidden" name="ml-submit" value="1"><input type="hidden" name="anticsrf" value="true">
      <button type="submit">Iscriviti</button>
      <p class="nl__nota">Nome, cognome ed email servono solo per spedirti la newsletter. Ricevi una email per confermare, e ti cancelli con un clic da ogni numero. <a href="/privacy#newsletter">Privacy</a>.</p>
      <p class="nl__esito" role="status" hidden></p>
    </form>
      <script src="/newsletter.js?v=2026-10-09" defer></script>
    </section>
'''

# ---------------------------------------------------------------- lingue ---
# Tutto il testo della pagina sta qui. Le frasi con dati sono funzioni.

def _ord_en(n):
    s = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{s}"

L = {
 "it": dict(
  slug="euribor-oggi", nome="Italiano", locale="it_IT", store="it", dec=",", migl=".", pct_sp="",
  euro=lambda s: f"{s} €", pb_u="pb", invariato="invariato", pb_lungo="punti base", nome_idx="Euribor",
  mesi=["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"],
  mesi_brevi=["gen","feb","mar","apr","mag","giu","lug","ago","set","ott","nov","dic"],
  giorni=["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"],
  data_lunga=lambda g, d, m, a: f"{g} {d} {m} {a}", data_media=lambda d, m, a: f"{d} {m} {a}", breve=lambda d, m: f"{d} {m}",
  tenor=["1 settimana","1 mese","3 mesi","6 mesi","12 mesi"],
  fermo=lambda D, v: f"Nel fixing di {D} l'Euribor a 3 mesi è rimasto fermo a {v}.",
  mosso=lambda D, su, n, v: f"Nel fixing di {D} l'Euribor a 3 mesi è {'salito' if su else 'sceso'} di {n}, a {v}.",
  serie=lambda k, su: f"È il {k}° {'rialzo' if su else 'ribasso'} di fila.",
  mese_pari=lambda d: f"Rispetto a un mese fa ({d}) è allo stesso livello.",
  mese=lambda su, n, d, v: f"In un mese è {'salito' if su else 'sceso'} di {n}: il {d} era a {v}.",
  minimo="È il valore più basso degli ultimi dodici mesi.", massimo="È il valore più alto degli ultimi dodici mesi.",
  forchetta=lambda a, da, b, db: f"Negli ultimi dodici mesi è andato da un minimo di {a} ({da}) a un massimo di {b} ({db}).",
  sopra=lambda v, sp: f"L'Euribor a 12 mesi ({v}) è sopra quello a 3 mesi di {sp}. Quando la scadenza lunga rende più di quella corta, il mercato non si aspetta tagli dei tassi nei prossimi mesi: semmai tassi stabili o in leggera salita.",
  sotto=lambda v, sp: f"L'Euribor a 12 mesi ({v}) è sotto quello a 3 mesi di {sp}. Quando la scadenza lunga rende meno di quella corta, il mercato si aspetta tassi più bassi nei prossimi mesi.",
  pari=lambda v, sp: f"L'Euribor a 12 mesi ({v}) e quello a 3 mesi sono quasi alla pari (differenza di {sp}): il mercato si aspetta tassi stabili nei prossimi mesi.",
  rata=lambda c, r: f"Su un mutuo a tasso variabile da {c} a 20 anni, indicizzato all'Euribor 3 mesi con uno spread dell'1%, la rata con l'ultimo fixing è di circa {r} al mese",
  rata_diff=lambda d, piu, v: f": {d} {'in più' if piu else 'in meno'} rispetto a un anno fa, quando l'indice era a {v}.",
  rata_uguale=", praticamente come un anno fa.",
  titolo=lambda b, v3, v12: f"Euribor oggi, {b}: 3 mesi {v3}, 12 mesi {v12}",
  descr=lambda D, v1, v3, v6, v12: f"Euribor di {D}: 1 mese {v1}, 3 mesi {v3}, 6 mesi {v6}, 12 mesi {v12}. Variazioni, grafico di un anno e cosa significa per la rata del mutuo.",
  h1="Euribor oggi", tutte_app="Tutte le app", privacy="Privacy e assistenza", lingua="Lingua",
  newsletter=NEWSLETTER_IT,
  tesi=lambda D: f"I tassi Euribor del <strong>fixing di {D}</strong>, con la variazione rispetto al giorno prima, il grafico dell'ultimo anno e <strong>cosa significa per la rata di un mutuo variabile</strong>. La pagina si aggiorna da sola ogni giorno lavorativo.",
  quando=lambda d, de, u: f"Euribor: fixing del {d} · €STR: {de} · variazioni in punti base ({u}) rispetto al fixing precedente",
  h2_lettura="La lettura di oggi", h2_var="Le variazioni", h2_grafico="Gli ultimi dodici mesi", h2_faq="Domande frequenti",
  colonne=["Tasso","Valore","Giorno","Settimana","Mese","Anno"],
  grafico_aria="Euribor 3 e 12 mesi, ultimi dodici mesi", leg3="Euribor 3 mesi", leg12="Euribor 12 mesi",
  invito_app=lambda u: f'<strong>Lo stesso, sul telefono.</strong> <a href="{u}">Euribor X</a> mostra i fixing di ogni giorno con i grafici storici e un simulatore di mutuo, anche senza rete. Gratis su iPhone e iPad.',
  invito_dash=lambda u: f'Per esplorare tutto lo storico e confrontarlo con il tasso BCE c\'è la <a href="{u}">dashboard BCE &amp; Euribor</a>.',
  scheda=[("Dati", "Euribor (EMMI) ed €STR (BCE), le stesse serie usate dall'app Euribor X"),
          ("Esempio di rata", "Mutuo da 100.000 € a 20 anni, rata mensile ad ammortamento francese, Euribor 3 mesi + 1%. È un esempio: la rata vera dipende da contratto, spread e calendario di revisione."),
          ("Aggiornamento", "Ogni giorno lavorativo, in automatico")],
  faq=[
   ("Che cos'è l'Euribor?", "È il tasso medio a cui le principali banche dell'area euro si prestano denaro senza garanzie. Lo calcola ogni giorno lavorativo l'EMMI (European Money Markets Institute) per cinque scadenze: 1 settimana, 1, 3, 6 e 12 mesi. È l'indice a cui è agganciata la maggior parte dei mutui e dei finanziamenti a tasso variabile in Italia."),
   ("Quale Euribor usa il mio mutuo?", "Lo trovi nel contratto, alla voce che descrive il tasso: di solito è l'Euribor a 1 o a 3 mesi, più uno spread fisso stabilito dalla banca. Il contratto dice anche ogni quanto la rata viene ricalcolata e quale fixing si usa, per esempio la media del mese precedente o il valore di un giorno preciso."),
   ("Quando viene pubblicato?", "L'EMMI pubblica l'Euribor ogni giorno lavorativo del calendario TARGET, verso le 11 ora di Bruxelles. Questa pagina si aggiorna in automatico quando il nuovo fixing è disponibile nei dati pubblici, di norma entro il giorno lavorativo successivo. Nei fine settimana e nei festivi TARGET non esce nessun fixing."),
   ("Che cos'è l'€STR?", "È il tasso a un giorno (overnight) del mercato monetario in euro, calcolato dalla Banca Centrale Europea. Misura il costo del denaro da un giorno all'altro ed è il riferimento più vicino alle decisioni della BCE; l'Euribor a 1 settimana gli si muove intorno."),
   ("Cosa vuol dire «pb»?", "Punti base: un centesimo di punto percentuale. Se l'Euribor passa dal 2,620% al 2,633% è salito di 1,3 punti base."),
  ]),
 "en": dict(
  slug="euribor-today", nome="English", locale="en_GB", store="gb", dec=".", migl=",", pct_sp="",
  euro=lambda s: f"€{s}", pb_u="bp", invariato="unchanged", pb_lungo="basis points", nome_idx="Euribor",
  mesi=["January","February","March","April","May","June","July","August","September","October","November","December"],
  mesi_brevi=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
  giorni=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
  data_lunga=lambda g, d, m, a: f"{g} {d} {m} {a}", data_media=lambda d, m, a: f"{d} {m} {a}", breve=lambda d, m: f"{d} {m}",
  tenor=["1 week","1 month","3 months","6 months","12 months"],
  fermo=lambda D, v: f"In the fixing of {D}, the 3-month Euribor was unchanged at {v}.",
  mosso=lambda D, su, n, v: f"In the fixing of {D}, the 3-month Euribor {'rose' if su else 'fell'} {n} to {v}.",
  serie=lambda k, su: f"That is the {_ord_en(k)} {'rise' if su else 'fall'} in a row.",
  mese_pari=lambda d: f"It is at the same level as a month ago ({d}).",
  mese=lambda su, n, d, v: f"Over the past month it has {'risen' if su else 'fallen'} {n}: on {d} it stood at {v}.",
  minimo="It is the lowest level of the past twelve months.", massimo="It is the highest level of the past twelve months.",
  forchetta=lambda a, da, b, db: f"Over the past twelve months it has ranged from a low of {a} ({da}) to a high of {b} ({db}).",
  sopra=lambda v, sp: f"The 12-month Euribor ({v}) is {sp} above the 3-month rate. When the longer maturity pays more than the shorter one, the market is not expecting rate cuts in the coming months: if anything, stable or slightly higher rates.",
  sotto=lambda v, sp: f"The 12-month Euribor ({v}) is {sp} below the 3-month rate. When the longer maturity pays less than the shorter one, the market expects lower rates in the coming months.",
  pari=lambda v, sp: f"The 12-month Euribor ({v}) and the 3-month rate are almost level (a difference of {sp}): the market expects stable rates in the coming months.",
  rata=lambda c, r: f"On a 20-year variable-rate mortgage of {c} tied to the 3-month Euribor with a 1% margin, the monthly payment at the latest fixing is about {r}",
  rata_diff=lambda d, piu, v: f": {d} {'more' if piu else 'less'} than a year ago, when the index stood at {v}.",
  rata_uguale=", practically the same as a year ago.",
  titolo=lambda b, v3, v12: f"Euribor today, {b}: 3-month {v3}, 12-month {v12}",
  descr=lambda D, v1, v3, v6, v12: f"Euribor rates for {D}: 1 month {v1}, 3 months {v3}, 6 months {v6}, 12 months {v12}. Changes, a one-year chart and what it means for a mortgage payment.",
  h1="Euribor today", tutte_app="All apps", privacy="Privacy and support", lingua="Language",
  tesi=lambda D: f"Euribor rates from the <strong>fixing of {D}</strong>, with the change from the day before, a chart of the past year and <strong>what it means for a variable-rate mortgage payment</strong>. The page updates itself every working day.",
  quando=lambda d, de, u: f"Euribor: fixing of {d} · €STR: {de} · changes in basis points ({u}) from the previous fixing",
  h2_lettura="Today's reading", h2_var="Changes", h2_grafico="The past twelve months", h2_faq="Frequently asked questions",
  colonne=["Rate","Value","Day","Week","Month","Year"],
  grafico_aria="3-month and 12-month Euribor, past twelve months", leg3="3-month Euribor", leg12="12-month Euribor",
  invito_app=lambda u: f'<strong>The same, on your phone.</strong> <a href="{u}">Euribor X</a> shows every day\'s fixings with historical charts and a mortgage simulator, even offline. Free on iPhone and iPad.',
  invito_dash=lambda u: f'To explore the full history and compare it with the ECB rate, there is the <a href="{u}">ECB &amp; Euribor dashboard</a>.',
  scheda=[("Data", "Euribor (EMMI) and €STR (ECB), the same series used by the Euribor X app"),
          ("Payment example", "€100,000 mortgage over 20 years, monthly annuity repayment, 3-month Euribor + 1%. It is an example: the real payment depends on the contract, the margin and the reset schedule."),
          ("Updates", "Every working day, automatically")],
  faq=[
   ("What is Euribor?", "It is the average rate at which the main banks in the euro area lend to each other without collateral. The EMMI (European Money Markets Institute) calculates it every working day for five maturities: 1 week and 1, 3, 6 and 12 months. In Italy, Spain, Portugal and other euro countries, most variable-rate mortgages and loans are tied to it."),
   ("Which Euribor does my mortgage use?", "It is in your contract, where the interest rate is described: usually a 1, 3, 6 or 12-month Euribor plus a fixed margin set by the bank. The contract also says how often the payment is reset and which fixing is used, for example the previous month's average or the value on a specific day."),
   ("When is it published?", "The EMMI publishes Euribor every TARGET working day, around 11:00 Brussels time. This page updates automatically once the new fixing is available in the public data, normally by the following working day. No fixing is published at weekends or on TARGET holidays."),
   ("What is €STR?", "It is the overnight rate of the euro money market, calculated by the European Central Bank. It measures the cost of money from one day to the next and is the benchmark closest to ECB decisions; the 1-week Euribor moves around it."),
   ("What does “bp” mean?", "Basis points: one hundredth of a percentage point. If Euribor goes from 2.620% to 2.633%, it has risen by 1.3 basis points."),
  ]),
 "fr": dict(
  slug="euribor-aujourdhui", nome="Français", locale="fr_FR", store="fr", dec=",", migl=NNBSP, pct_sp=NBSP,
  euro=lambda s: f"{s}{NBSP}€", pb_u="pb", invariato="inchangé", pb_lungo="points de base", nome_idx="Euribor",
  mesi=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"],
  mesi_brevi=["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."],
  giorni=["lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"],
  data_lunga=lambda g, d, m, a: f"{g} {d} {m} {a}", data_media=lambda d, m, a: f"{d} {m} {a}", breve=lambda d, m: f"{d} {m}",
  tenor=["1 semaine","1 mois","3 mois","6 mois","12 mois"],
  fermo=lambda D, v: f"Lors du fixing du {D}, l'Euribor à 3 mois est resté stable à {v}.",
  mosso=lambda D, su, n, v: f"Lors du fixing du {D}, l'Euribor à 3 mois a {'augmenté' if su else 'baissé'} de {n}, à {v}.",
  serie=lambda k, su: f"C'est la {k}e {'hausse' if su else 'baisse'} d'affilée.",
  mese_pari=lambda d: f"Il est au même niveau qu'il y a un mois ({d}).",
  mese=lambda su, n, d, v: f"En un mois, il a {'augmenté' if su else 'baissé'} de {n} : le {d}, il était à {v}.",
  minimo="C'est le niveau le plus bas des douze derniers mois.", massimo="C'est le niveau le plus haut des douze derniers mois.",
  forchetta=lambda a, da, b, db: f"Sur les douze derniers mois, il est allé d'un plus bas de {a} ({da}) à un plus haut de {b} ({db}).",
  sopra=lambda v, sp: f"L'Euribor à 12 mois ({v}) dépasse celui à 3 mois de {sp}. Quand l'échéance longue rapporte plus que la courte, le marché n'anticipe pas de baisse des taux dans les prochains mois : plutôt des taux stables ou en légère hausse.",
  sotto=lambda v, sp: f"L'Euribor à 12 mois ({v}) est inférieur à celui à 3 mois de {sp}. Quand l'échéance longue rapporte moins que la courte, le marché anticipe des taux plus bas dans les prochains mois.",
  pari=lambda v, sp: f"L'Euribor à 12 mois ({v}) et celui à 3 mois sont presque au même niveau (écart de {sp}) : le marché anticipe des taux stables dans les prochains mois.",
  rata=lambda c, r: f"Pour un prêt immobilier à taux variable de {c} sur 20 ans, indexé sur l'Euribor 3 mois avec une marge de 1{NBSP}%, la mensualité au dernier fixing est d'environ {r}",
  rata_diff=lambda d, piu, v: f" : {d} de {'plus' if piu else 'moins'} qu'il y a un an, quand l'indice était à {v}.",
  rata_uguale=", pratiquement comme il y a un an.",
  titolo=lambda b, v3, v12: f"Euribor aujourd'hui, {b} : 3 mois {v3}, 12 mois {v12}",
  descr=lambda D, v1, v3, v6, v12: f"Euribor du {D} : 1 mois {v1}, 3 mois {v3}, 6 mois {v6}, 12 mois {v12}. Variations, graphique sur un an et ce que cela signifie pour la mensualité d'un prêt.",
  h1="Euribor aujourd'hui", tutte_app="Toutes les apps", privacy="Confidentialité et assistance", lingua="Langue",
  tesi=lambda D: f"Les taux Euribor du <strong>fixing du {D}</strong>, avec la variation par rapport à la veille, le graphique de l'année écoulée et <strong>ce que cela signifie pour la mensualité d'un prêt à taux variable</strong>. La page se met à jour toute seule chaque jour ouvré.",
  quando=lambda d, de, u: f"Euribor : fixing du {d} · €STR : {de} · variations en points de base ({u}) par rapport au fixing précédent",
  h2_lettura="La lecture du jour", h2_var="Les variations", h2_grafico="Les douze derniers mois", h2_faq="Questions fréquentes",
  colonne=["Taux","Valeur","Jour","Semaine","Mois","Année"],
  grafico_aria="Euribor 3 et 12 mois, douze derniers mois", leg3="Euribor 3 mois", leg12="Euribor 12 mois",
  invito_app=lambda u: f'<strong>La même chose, sur votre téléphone.</strong> <a href="{u}">Euribor X</a> affiche les fixings de chaque jour avec les graphiques historiques et un simulateur de prêt, même hors ligne. Gratuit sur iPhone et iPad.',
  invito_dash=lambda u: f'Pour explorer tout l\'historique et le comparer au taux de la BCE, il y a le <a href="{u}">tableau de bord BCE &amp; Euribor</a>.',
  scheda=[("Données", "Euribor (EMMI) et €STR (BCE), les mêmes séries que celles de l'app Euribor X"),
          ("Exemple de mensualité", f"Prêt de 100{NNBSP}000{NBSP}€ sur 20 ans, mensualités constantes, Euribor 3 mois + 1{NBSP}%. C'est un exemple : la mensualité réelle dépend du contrat, de la marge et du calendrier de révision."),
          ("Mise à jour", "Chaque jour ouvré, automatiquement")],
  faq=[
   ("Qu'est-ce que l'Euribor ?", "C'est le taux moyen auquel les principales banques de la zone euro se prêtent de l'argent sans garantie. L'EMMI (European Money Markets Institute) le calcule chaque jour ouvré pour cinq échéances : 1 semaine, 1, 3, 6 et 12 mois. En Italie, en Espagne, au Portugal et dans d'autres pays de la zone euro, la plupart des prêts à taux variable y sont indexés."),
   ("Quel Euribor utilise mon prêt ?", "Il figure dans le contrat, là où le taux est décrit : en général un Euribor à 1, 3, 6 ou 12 mois, plus une marge fixe définie par la banque. Le contrat indique aussi à quelle fréquence la mensualité est révisée et quel fixing est retenu, par exemple la moyenne du mois précédent ou la valeur d'un jour précis."),
   ("Quand est-il publié ?", "L'EMMI publie l'Euribor chaque jour ouvré du calendrier TARGET, vers 11 heures, heure de Bruxelles. Cette page se met à jour automatiquement dès que le nouveau fixing est disponible dans les données publiques, normalement le jour ouvré suivant au plus tard. Aucun fixing n'est publié le week-end ni les jours fériés TARGET."),
   ("Qu'est-ce que l'€STR ?", "C'est le taux au jour le jour (overnight) du marché monétaire en euros, calculé par la Banque centrale européenne. Il mesure le coût de l'argent d'un jour à l'autre et c'est la référence la plus proche des décisions de la BCE ; l'Euribor à 1 semaine évolue autour de lui."),
   ("Que signifie « pb » ?", f"Points de base : un centième de point de pourcentage. Si l'Euribor passe de 2,620{NBSP}% à 2,633{NBSP}%, il a augmenté de 1,3 point de base."),
  ]),
 "de": dict(
  slug="euribor-heute", nome="Deutsch", locale="de_DE", store="de", dec=",", migl=".", pct_sp=NBSP,
  euro=lambda s: f"{s}{NBSP}€", pb_u="Bp", invariato="unverändert", pb_lungo="Basispunkte", nome_idx="Euribor",
  mesi=["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"],
  mesi_brevi=["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],
  giorni=["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],
  data_lunga=lambda g, d, m, a: f"{g}, {d}. {m} {a}", data_media=lambda d, m, a: f"{d}. {m} {a}", breve=lambda d, m: f"{d}. {m}",
  tenor=["1 Woche","1 Monat","3 Monate","6 Monate","12 Monate"],
  fermo=lambda D, v: f"Beim Fixing vom {D} blieb der 3-Monats-Euribor unverändert bei {v}.",
  mosso=lambda D, su, n, v: f"Beim Fixing vom {D} ist der 3-Monats-Euribor um {n} auf {v} {'gestiegen' if su else 'gesunken'}.",
  serie=lambda k, su: f"Das ist der {k}. {'Anstieg' if su else 'Rückgang'} in Folge.",
  mese_pari=lambda d: f"Er liegt auf demselben Niveau wie vor einem Monat ({d}).",
  mese=lambda su, n, d, v: f"Innerhalb eines Monats ist er um {n} {'gestiegen' if su else 'gesunken'}: Am {d} lag er bei {v}.",
  minimo="Das ist der tiefste Stand der letzten zwölf Monate.", massimo="Das ist der höchste Stand der letzten zwölf Monate.",
  forchetta=lambda a, da, b, db: f"In den letzten zwölf Monaten bewegte er sich zwischen einem Tief von {a} ({da}) und einem Hoch von {b} ({db}).",
  sopra=lambda v, sp: f"Der 12-Monats-Euribor ({v}) liegt {sp} über dem 3-Monats-Satz. Wenn die längere Laufzeit mehr abwirft als die kürzere, erwartet der Markt in den nächsten Monaten keine Zinssenkungen, eher stabile oder leicht steigende Zinsen.",
  sotto=lambda v, sp: f"Der 12-Monats-Euribor ({v}) liegt {sp} unter dem 3-Monats-Satz. Wenn die längere Laufzeit weniger abwirft als die kürzere, erwartet der Markt in den nächsten Monaten niedrigere Zinsen.",
  pari=lambda v, sp: f"Der 12-Monats-Euribor ({v}) und der 3-Monats-Satz liegen fast gleichauf (Abstand {sp}): Der Markt erwartet in den nächsten Monaten stabile Zinsen.",
  rata=lambda c, r: f"Bei einem variabel verzinsten Darlehen über {c} mit 20 Jahren Laufzeit, gebunden an den 3-Monats-Euribor plus 1{NBSP}% Aufschlag, beträgt die Monatsrate beim letzten Fixing rund {r}",
  rata_diff=lambda d, piu, v: f": {d} {'mehr' if piu else 'weniger'} als vor einem Jahr, als der Index bei {v} lag.",
  rata_uguale=", praktisch so viel wie vor einem Jahr.",
  titolo=lambda b, v3, v12: f"Euribor heute, {b}: 3 Monate {v3}, 12 Monate {v12}",
  descr=lambda D, v1, v3, v6, v12: f"Euribor vom {D}: 1 Monat {v1}, 3 Monate {v3}, 6 Monate {v6}, 12 Monate {v12}. Veränderungen, Jahreschart und was das für die Kreditrate bedeutet.",
  h1="Euribor heute", tutte_app="Alle Apps", privacy="Datenschutz und Support", lingua="Sprache",
  tesi=lambda D: f"Die Euribor-Sätze vom <strong>Fixing am {D}</strong>, mit der Veränderung zum Vortag, dem Chart des letzten Jahres und <strong>was das für die Rate eines variablen Darlehens bedeutet</strong>. Die Seite aktualisiert sich an jedem Arbeitstag von selbst.",
  quando=lambda d, de, u: f"Euribor: Fixing vom {d} · €STR: {de} · Veränderungen in Basispunkten ({u}) zum vorherigen Fixing",
  h2_lettura="Die Lage heute", h2_var="Veränderungen", h2_grafico="Die letzten zwölf Monate", h2_faq="Häufige Fragen",
  colonne=["Satz","Wert","Tag","Woche","Monat","Jahr"],
  grafico_aria="Euribor 3 und 12 Monate, letzte zwölf Monate", leg3="Euribor 3 Monate", leg12="Euribor 12 Monate",
  invito_app=lambda u: f'<strong>Dasselbe auf dem Telefon.</strong> <a href="{u}">Euribor X</a> zeigt die Fixings jedes Tages mit historischen Charts und einem Kreditrechner, auch offline. Kostenlos für iPhone und iPad.',
  invito_dash=lambda u: f'Die ganze Historie im Vergleich mit dem EZB-Zins zeigt das <a href="{u}">EZB- &amp; Euribor-Dashboard</a>.',
  scheda=[("Daten", "Euribor (EMMI) und €STR (EZB), dieselben Reihen wie in der App Euribor X"),
          ("Ratenbeispiel", f"Darlehen über 100.000{NBSP}€ mit 20 Jahren Laufzeit, Annuitätenrate monatlich, 3-Monats-Euribor + 1{NBSP}%. Das ist ein Beispiel: Die tatsächliche Rate hängt von Vertrag, Aufschlag und Anpassungsterminen ab."),
          ("Aktualisierung", "An jedem Arbeitstag, automatisch")],
  faq=[
   ("Was ist der Euribor?", "Der durchschnittliche Zinssatz, zu dem sich die wichtigsten Banken im Euroraum ohne Sicherheiten Geld leihen. Das EMMI (European Money Markets Institute) berechnet ihn an jedem Arbeitstag für fünf Laufzeiten: 1 Woche sowie 1, 3, 6 und 12 Monate. In Italien, Spanien, Portugal und anderen Euroländern sind die meisten variabel verzinsten Kredite daran gebunden."),
   ("Welchen Euribor nutzt mein Kredit?", "Das steht im Vertrag, dort, wo der Zinssatz beschrieben ist: meist ein Euribor mit 1, 3, 6 oder 12 Monaten plus ein fester Aufschlag der Bank. Der Vertrag legt auch fest, wie oft die Rate angepasst wird und welches Fixing gilt, etwa der Durchschnitt des Vormonats oder der Wert eines bestimmten Tages."),
   ("Wann wird er veröffentlicht?", "Das EMMI veröffentlicht den Euribor an jedem TARGET-Arbeitstag gegen 11 Uhr Brüsseler Zeit. Diese Seite aktualisiert sich automatisch, sobald das neue Fixing in den öffentlichen Daten verfügbar ist, normalerweise bis zum folgenden Arbeitstag. An Wochenenden und TARGET-Feiertagen gibt es kein Fixing."),
   ("Was ist der €STR?", "Der Tagesgeldsatz (Overnight) des Euro-Geldmarkts, berechnet von der Europäischen Zentralbank. Er misst die Kosten für Geld von einem Tag auf den nächsten und ist der Referenzwert, der den EZB-Entscheidungen am nächsten liegt; der 1-Wochen-Euribor bewegt sich um ihn herum."),
   ("Was bedeutet „Bp“?", f"Basispunkte: ein Hundertstel Prozentpunkt. Steigt der Euribor von 2,620{NBSP}% auf 2,633{NBSP}%, ist er um 1,3 Basispunkte gestiegen."),
  ]),
 "es": dict(
  slug="euribor-hoy", nome="Español", locale="es_ES", store="es", dec=",", migl=".", pct_sp=NBSP,
  euro=lambda s: f"{s}{NBSP}€", pb_u="pb", invariato="sin cambios", pb_lungo="puntos básicos", nome_idx="Euríbor",
  mesi=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],
  mesi_brevi=["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"],
  giorni=["lunes","martes","miércoles","jueves","viernes","sábado","domingo"],
  data_lunga=lambda g, d, m, a: f"{g} {d} de {m} de {a}", data_media=lambda d, m, a: f"{d} de {m} de {a}", breve=lambda d, m: f"{d} de {m}",
  tenor=["1 semana","1 mes","3 meses","6 meses","12 meses"],
  fermo=lambda D, v: f"En el fixing del {D}, el Euríbor a 3 meses se mantuvo en el {v}.",
  mosso=lambda D, su, n, v: f"En el fixing del {D}, el Euríbor a 3 meses {'subió' if su else 'bajó'} {n}, hasta el {v}.",
  serie=lambda k, su: f"Es la {k}.ª {'subida' if su else 'bajada'} consecutiva.",
  mese_pari=lambda d: f"Está al mismo nivel que hace un mes ({d}).",
  mese=lambda su, n, d, v: f"En un mes ha {'subido' if su else 'bajado'} {n}: el {d} estaba en el {v}.",
  minimo="Es el nivel más bajo de los últimos doce meses.", massimo="Es el nivel más alto de los últimos doce meses.",
  forchetta=lambda a, da, b, db: f"En los últimos doce meses ha oscilado entre un mínimo del {a} ({da}) y un máximo del {b} ({db}).",
  sopra=lambda v, sp: f"El Euríbor a 12 meses ({v}) está {sp} por encima del de 3 meses. Cuando el plazo largo rinde más que el corto, el mercado no espera bajadas de tipos en los próximos meses, sino tipos estables o en ligera subida.",
  sotto=lambda v, sp: f"El Euríbor a 12 meses ({v}) está {sp} por debajo del de 3 meses. Cuando el plazo largo rinde menos que el corto, el mercado espera tipos más bajos en los próximos meses.",
  pari=lambda v, sp: f"El Euríbor a 12 meses ({v}) y el de 3 meses están casi igualados (diferencia de {sp}): el mercado espera tipos estables en los próximos meses.",
  rata=lambda c, r: f"En una hipoteca variable de {c} a 20 años, referenciada al Euríbor a 3 meses con un diferencial del 1{NBSP}%, la cuota mensual con el último fixing es de unos {r}",
  rata_diff=lambda d, piu, v: f": {d} {'más' if piu else 'menos'} que hace un año, cuando el índice estaba en el {v}.",
  rata_uguale=", prácticamente igual que hace un año.",
  titolo=lambda b, v3, v12: f"Euríbor hoy, {b}: 3 meses {v3}, 12 meses {v12}",
  descr=lambda D, v1, v3, v6, v12: f"Euríbor del {D}: 1 mes {v1}, 3 meses {v3}, 6 meses {v6}, 12 meses {v12}. Variaciones, gráfico de un año y qué significa para la cuota de la hipoteca.",
  h1="Euríbor hoy", tutte_app="Todas las apps", privacy="Privacidad y soporte", lingua="Idioma",
  tesi=lambda D: f"Los tipos Euríbor del <strong>fixing del {D}</strong>, con la variación respecto al día anterior, el gráfico del último año y <strong>qué significa para la cuota de una hipoteca variable</strong>. La página se actualiza sola cada día hábil.",
  quando=lambda d, de, u: f"Euríbor: fixing del {d} · €STR: {de} · variaciones en puntos básicos ({u}) respecto al fixing anterior",
  h2_lettura="La lectura de hoy", h2_var="Las variaciones", h2_grafico="Los últimos doce meses", h2_faq="Preguntas frecuentes",
  colonne=["Tipo","Valor","Día","Semana","Mes","Año"],
  grafico_aria="Euríbor a 3 y 12 meses, últimos doce meses", leg3="Euríbor 3 meses", leg12="Euríbor 12 meses",
  invito_app=lambda u: f'<strong>Lo mismo, en el móvil.</strong> <a href="{u}">Euribor X</a> muestra los fixings de cada día con gráficos históricos y un simulador de hipoteca, incluso sin conexión. Gratis en iPhone y iPad.',
  invito_dash=lambda u: f'Para explorar todo el histórico y compararlo con el tipo del BCE está el <a href="{u}">panel BCE &amp; Euríbor</a>.',
  scheda=[("Datos", "Euríbor (EMMI) y €STR (BCE), las mismas series que usa la app Euribor X"),
          ("Ejemplo de cuota", f"Hipoteca de 100.000{NBSP}€ a 20 años, cuota mensual con sistema francés, Euríbor 3 meses + 1{NBSP}%. Es un ejemplo: la cuota real depende del contrato, el diferencial y el calendario de revisión."),
          ("Actualización", "Cada día hábil, automáticamente")],
  faq=[
   ("¿Qué es el Euríbor?", "Es el tipo de interés medio al que los principales bancos de la zona euro se prestan dinero sin garantías. Lo calcula cada día hábil el EMMI (European Money Markets Institute) para cinco plazos: 1 semana y 1, 3, 6 y 12 meses. En España la mayoría de las hipotecas variables están referenciadas al Euríbor a 12 meses."),
   ("¿Qué Euríbor usa mi hipoteca?", "Figura en la escritura, donde se describe el tipo de interés: normalmente el Euríbor a 12 meses en España, o a 1, 3 o 6 meses en otros países, más un diferencial fijo que establece el banco. El contrato indica también cada cuánto se revisa la cuota y qué valor se toma, por ejemplo la media del mes anterior o el de un día concreto."),
   ("¿Cuándo se publica?", "El EMMI publica el Euríbor cada día hábil del calendario TARGET, hacia las 11 hora de Bruselas. Esta página se actualiza sola cuando el nuevo fixing está disponible en los datos públicos, normalmente como muy tarde el día hábil siguiente. Los fines de semana y los festivos TARGET no se publica ningún fixing."),
   ("¿Qué es el €STR?", "Es el tipo a un día (overnight) del mercado monetario en euros, que calcula el Banco Central Europeo. Mide el coste del dinero de un día para otro y es la referencia más cercana a las decisiones del BCE; el Euríbor a 1 semana se mueve en torno a él."),
   ("¿Qué significa «pb»?", f"Puntos básicos: una centésima de punto porcentual. Si el Euríbor pasa del 2,620{NBSP}% al 2,633{NBSP}%, ha subido 1,3 puntos básicos."),
  ]),
}
LINGUE = ["it", "en", "fr", "de", "es"]


def url(lg):
    return f"{SITO}/finanza/{L[lg]['slug']}"


# --------------------------------------------------------------- dati -----

def scarica(nome):
    with urllib.request.urlopen(BASE + nome, timeout=30) as r:
        testo = r.read().decode("utf-8-sig")
    serie = {}
    for riga in csv.DictReader(io.StringIO(testo)):
        g, m, a = riga["Date"].split(".")
        d = date(int(a), int(m), int(g))
        for k, v in riga.items():
            if k in ("Date", "Week day") or not (v or "").strip():
                continue
            serie.setdefault(k, {})[d] = float(v)
    return {k: sorted(v.items()) for k, v in serie.items()}


def al(serie, giorno):
    """Ultimo valore disponibile alla data indicata o prima."""
    ultimo = None
    for d, v in serie:
        if d > giorno:
            break
        ultimo = (d, v)
    return ultimo


def meno_mesi(d, n):
    m = d.month - n
    a = d.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    giorni = [31, 29 if a % 4 == 0 and (a % 100 or a % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(a, m, min(d.day, giorni))


def rata(indice, spread=1.0, capitale=100_000, anni=20):
    tasso = max(indice + spread, 0) / 100 / 12
    n = anni * 12
    return capitale / n if tasso == 0 else capitale * tasso / (1 - (1 + tasso) ** -n)


# ------------------------------------------------------------ formati -----

class F:
    """Numeri e date nella lingua scelta."""
    def __init__(self, lg):
        self.t = L[lg]

    def num(self, v, cifre):
        s = f"{abs(v):,.{cifre}f}".replace(",", "\0").replace(".", self.t["dec"]).replace("\0", self.t["migl"])
        return ("−" if v < 0 else "") + s

    def pct(self, v, cifre=3):
        return self.num(v, cifre) + self.t["pct_sp"] + "%"

    def pb(self, delta, prosa=False):
        x = round(delta * 100, 1)
        if abs(x) < 0.05:
            return self.t["invariato"]
        intero = prosa and abs(x) == int(abs(x))
        s = self.num(abs(x), 0 if intero else 1)
        return ("+" if x > 0 else "−") + s + NBSP + self.t["pb_u"]

    def pb_n(self, delta):
        """Variazione senza segno, per le frasi."""
        return self.pb(abs(delta), True)[1:]

    def euro(self, x):
        return self.t["euro"](self.num(x, 0))

    def data_lunga(self, d):
        return self.t["data_lunga"](self.t["giorni"][d.weekday()], d.day, self.t["mesi"][d.month - 1], d.year)

    def data_media(self, d):
        return self.t["data_media"](d.day, self.t["mesi"][d.month - 1], d.year)


def freccia(delta):
    x = round(delta * 100, 1)
    return "▲" if x > 0.05 else ("▼" if x < -0.05 else "=")


# ------------------------------------------------------------- testo ------

def lettura(f, s3, s12):
    t = f.t
    d0, v = s3[-1]
    prec = s3[-2][1]
    frasi = []
    diff = v - prec
    D = f.data_lunga(d0)
    if abs(diff) < 0.0005:
        frasi.append(t["fermo"](D, f.pct(v)))
    else:
        frasi.append(t["mosso"](D, diff > 0, f.pb_n(diff), f.pct(v)))
        segno, serie = (1 if diff > 0 else -1), 0
        for i in range(len(s3) - 1, 0, -1):
            dd = s3[i][1] - s3[i - 1][1]
            if abs(dd) < 0.0005 or (dd > 0) != (segno > 0):
                break
            serie += 1
        if serie >= 3:
            frasi.append(t["serie"](serie, segno > 0))
    rif_m = al(s3, meno_mesi(d0, 1))
    if rif_m:
        dm = v - rif_m[1]
        if abs(dm) < 0.0005:
            frasi.append(t["mese_pari"](f.data_media(rif_m[0])))
        else:
            frasi.append(t["mese"](dm > 0, f.pb_n(dm), f.data_media(rif_m[0]), f.pct(rif_m[1])))
    anno = [(d, x) for d, x in s3 if d > d0 - timedelta(days=365)]
    dmin, vmin = min(anno, key=lambda q: (q[1], -q[0].toordinal()))
    dmax, vmax = max(anno, key=lambda q: (q[1], q[0].toordinal()))
    if abs(v - vmin) < 0.0005 and dmin == d0:
        frasi.append(t["minimo"])
    elif abs(v - vmax) < 0.0005 and dmax == d0:
        frasi.append(t["massimo"])
    else:
        frasi.append(t["forchetta"](f.pct(vmin), f.data_media(dmin), f.pct(vmax), f.data_media(dmax)))
    p1 = " ".join(frasi)

    v12 = al(s12, d0)[1]
    sp = (v12 - v) * 100
    sp_txt = f"{f.num(abs(sp), 0)} {t['pb_lungo']}"
    if sp > 10:
        p2 = t["sopra"](f.pct(v12), sp_txt)
    elif sp < -10:
        p2 = t["sotto"](f.pct(v12), sp_txt)
    else:
        p2 = t["pari"](f.pct(v12), sp_txt)

    r_oggi = rata(v)
    rif_a = al(s3, d0 - timedelta(days=365))
    p3 = t["rata"](f.euro(100000), f.euro(r_oggi))
    if rif_a:
        dr = r_oggi - rata(rif_a[1])
        p3 += t["rata_diff"](f.euro(abs(dr)), dr > 0, f.pct(rif_a[1])) if abs(dr) >= 1 else t["rata_uguale"]
    else:
        p3 += "."
    return [p1, p2, p3]


def grafico(f, serie_12m, d0):
    inizio = d0 - timedelta(days=365)
    linee = [(k, [(d, v) for d, v in serie_12m[k] if d >= inizio]) for k in ("3M", "12M")]
    tutti = [v for _, s in linee for _, v in s]
    passo = next(p for p in (0.1, 0.2, 0.25, 0.5, 1.0) if (max(tutti) - min(tutti)) / p <= 5)
    lo, hi = math.floor(min(tutti) / passo) * passo, math.ceil(max(tutti) / passo) * passo
    W, H, sx, dx, su, giu = 1000, 320, 56, 16, 16, 34
    def x(d): return sx + (d - inizio).days / 365 * (W - sx - dx)
    def y(v): return su + (hi - v) / (hi - lo) * (H - su - giu)
    parti = [f'<svg class="grafico" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(f.t["grafico_aria"])}">']
    for i in range(round((hi - lo) / passo) + 1):
        v = lo + passo * i
        parti.append(f'<line x1="{sx}" x2="{W - dx}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="g-riga"/>'
                     f'<text x="{sx - 8}" y="{y(v) + 4:.1f}" class="g-asse" text-anchor="end">{f.pct(v, 2)}</text>')
    m = date(inizio.year, inizio.month, 1)
    while m <= d0:
        if m >= inizio and (m.month - 1) % 3 == 0:
            parti.append(f'<text x="{x(m):.1f}" y="{H - 10}" class="g-asse" text-anchor="middle">{f.t["mesi_brevi"][m.month - 1]} {str(m.year)[2:]}</text>')
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    for k, s in linee:
        punti = " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in s)
        parti.append(f'<polyline points="{punti}" class="g-linea g-{k.lower()}"/>')
    parti.append("</svg>")
    return "\n".join(parti)


def pagina(lg, eur, est):
    f = F(lg)
    t = f.t
    E = lambda s: html.escape(s, quote=False)
    s3 = eur["3M"]
    d0, v3 = s3[-1]
    v12 = al(eur["12M"], d0)[1]
    righe, cifre = [], []
    for k, nome in zip(["1W", "1M", "3M", "6M", "12M"], t["tenor"]):
        s = eur.get(k, [])
        u = al(s, d0)
        if not u:
            continue
        idx = [d for d, _ in s].index(u[0])
        prec = s[idx - 1][1] if idx else u[1]
        def var(rif):
            r = al(s, rif)
            return f.pb(u[1] - r[1]) if r else "—"
        righe.append(f"<tr><th scope=\"row\">{t['nome_idx']} {nome}</th><td class=\"num\">{f.pct(u[1])}</td>"
                     f"<td class=\"num\">{f.pb(u[1] - prec)}</td><td class=\"num\">{var(u[0] - timedelta(days=7))}</td>"
                     f"<td class=\"num\">{var(meno_mesi(u[0], 1))}</td><td class=\"num\">{var(u[0] - timedelta(days=365))}</td></tr>")
        cifre.append(f'<div class="cifra"><div class="cifra__nome">{nome}</div><div class="cifra__valore">{f.pct(u[1])}</div>'
                     f'<div class="cifra__var">{freccia(u[1] - prec)} {f.pb(u[1] - prec)}</div></div>')
    se = est["ON"]
    de, ve = se[-1]
    pe = se[-2][1]
    cifre.insert(0, f'<div class="cifra"><div class="cifra__nome">€STR</div><div class="cifra__valore">{f.pct(ve)}</div>'
                    f'<div class="cifra__var">{freccia(ve - pe)} {f.pb(ve - pe)}</div></div>')
    righe.append(f"<tr><th scope=\"row\">€STR <span class=\"nota\">({f.data_media(de)})</span></th><td class=\"num\">{f.pct(ve)}</td>"
                 f"<td class=\"num\">{f.pb(ve - pe)}</td><td class=\"num\">{f.pb(ve - al(se, de - timedelta(days=7))[1])}</td>"
                 f"<td class=\"num\">{f.pb(ve - al(se, meno_mesi(de, 1))[1])}</td><td class=\"num\">{f.pb(ve - al(se, de - timedelta(days=365))[1])}</td></tr>")
    p = lettura(f, s3, eur["12M"])
    titolo = t["titolo"](t["breve"](d0.day, t["mesi"][d0.month - 1]), f.pct(v3), f.pct(v12))
    descr = t["descr"](f.data_lunga(d0), f.pct(al(eur["1M"], d0)[1]), f.pct(v3), f.pct(al(eur["6M"], d0)[1]), f.pct(v12))
    faq_html = "\n".join(f"    <h3>{E(q)}</h3>\n    <p>{E(a)}</p>" for q, a in t["faq"])
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lg, "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]},
        ensure_ascii=False)
    alternativi = "\n".join(f'<link rel="alternate" hreflang="{x}" href="{url(x)}">' for x in LINGUE) + \
        f'\n<link rel="alternate" hreflang="x-default" href="{url("en")}">'
    lingue = " ".join(
        f'<strong lang="{x}">{L[x]["nome"]}</strong>' if x == lg else
        f'<a href="/finanza/{L[x]["slug"]}" hreflang="{x}" lang="{x}">{L[x]["nome"]}</a>' for x in LINGUE)
    app_store = f"https://apps.apple.com/{t['store']}/app/euribor-x-tassi-e-mutuo/id{APP_ID}"
    casa = "/" if lg == "it" else f"/{lg}/"   # home del sito nella lingua della pagina
    scheda = "\n".join(f"      <div><dt>{E(a)}</dt><dd>{E(b)}</dd></div>" for a, b in t["scheda"])
    return f"""<!DOCTYPE html>
<html lang="{lg}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{html.escape(titolo)}</title>
<meta name="description" content="{html.escape(descr)}">
<meta property="og:title" content="{html.escape(titolo)}">
<meta property="og:description" content="{html.escape(descr)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url(lg)}">
<meta property="og:image" content="https://bacchin.app/og.png">
<meta property="og:locale" content="{t['locale']}">
<meta name="theme-color" content="#171A1F">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23171A1F'/%3E%3Ccircle cx='32' cy='32' r='11' fill='%23F2A93B'/%3E%3C/svg%3E">
<link rel="stylesheet" href="/fonts/fonts.css">
<link rel="stylesheet" href="/stile.css?v={CSS_V}">
<link rel="canonical" href="{url(lg)}">
{alternativi}
<script type="application/ld+json">{faq_ld}</script>
<style>
  .dato-grande__griglia {{ grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }}
  .cifra__var {{ font-family: var(--dato); font-size: 12px; color: var(--nebbia); margin-top: 2px; white-space: nowrap; }}
  .tabella {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 15px; }}
  .tabella th, .tabella td {{ padding: 10px 8px; border-bottom: 1px solid var(--linea); text-align: left; }}
  .tabella thead th {{ font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--nebbia); font-weight: 600; }}
  .tabella .num {{ font-family: var(--dato); text-align: right; white-space: nowrap; }}
  .tabella .nota {{ color: var(--nebbia); font-size: 13px; font-weight: 400; }}
  .scorre {{ overflow-x: auto; }}
  @media (max-width: 700px) {{
    .tabella {{ font-size: 13.5px; }}
    .tabella th, .tabella td {{ padding: 9px 5px; }}
    .tabella tr > :nth-child(4), .tabella tr > :nth-child(6) {{ display: none; }}
    .tabella .nota {{ display: block; }}
  }}
  .grafico {{ width: 100%; height: auto; margin-top: 8px; }}
  .g-riga {{ stroke: var(--linea); stroke-width: 1; }}
  .g-asse {{ fill: var(--nebbia); font-family: var(--dato); font-size: 13px; }}
  .g-linea {{ fill: none; stroke-width: 2.5; stroke-linejoin: round; }}
  .g-3m {{ stroke: var(--ambra); }}
  .g-12m {{ stroke: var(--gesso); opacity: .75; }}
  .legenda {{ font-family: var(--dato); font-size: 12px; color: var(--nebbia); margin-top: 6px; }}
  .legenda .a {{ color: var(--ambra); }} .legenda .g {{ color: var(--gesso); }}
  .racconto h3 {{ font-size: 17px; margin: 22px 0 6px; }}
  .invito {{ margin-top: 36px; padding: 22px; background: var(--pannello); border: 1px solid var(--linea); border-radius: 14px; }}
  .invito a {{ color: var(--ambra); }}
  .lingue {{ margin-top: 18px; display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 14px; color: var(--nebbia); }}
  .lingue a {{ color: var(--nebbia); text-decoration: none; border-bottom: 1px solid var(--linea); }}
  .lingue a:hover {{ color: var(--ambra); border-color: var(--ambra); }}
  .lingue strong {{ color: var(--gesso); font-weight: 600; }}
</style>
</head>
<body>
<div class="foglio">

  <header class="testata">
    <a class="etichetta" href="{casa}">Fabrizio Bacchin</a>
    <a class="etichetta" href="{casa}#t-app">{t['tutte_app']}</a>
  </header>

  <div class="app-hero">
    <h1>{t['h1']}</h1>
    <p class="tesi">{t['tesi'](f.data_lunga(d0))}</p>
    <nav class="lingue" aria-label="{t['lingua']}">{lingue}</nav>
    <div class="dato-grande">
      <div class="dato-grande__griglia">
        {''.join(cifre)}
      </div>
      <div class="dato-grande__quando">{t['quando'](f.data_media(d0), f.data_media(de), t['pb_u'])}</div>
    </div>
  </div>

  <div class="racconto">
    <h2>{t['h2_lettura']}</h2>
    <p>{E(p[0])}</p>
    <p>{E(p[1])}</p>
    <p>{E(p[2])}</p>

    <h2>{t['h2_var']}</h2>
    <div class="scorre">
    <table class="tabella">
      <thead><tr><th scope="col">{t['colonne'][0]}</th>{''.join(f'<th scope="col" class="num">{c}</th>' for c in t['colonne'][1:])}</tr></thead>
      <tbody>
      {''.join(righe)}
      </tbody>
    </table>
    </div>

    <h2>{t['h2_grafico']}</h2>
    {grafico(f, eur, d0)}
    <p class="legenda"><span class="a">━ {t['leg3']}</span> &nbsp; <span class="g">━ {t['leg12']}</span></p>

    <div class="invito">
      <p>{t['invito_app'](app_store)}</p>
      <p>{t['invito_dash'](casa.rstrip('/') + DASHBOARD)}</p>
    </div>
{t.get('newsletter', '')}
    <h2>{t['h2_faq']}</h2>
{faq_html}

    <dl class="scheda-tecnica">
{scheda}
    </dl>
  </div>

  <footer class="piede">
    <span class="etichetta">© {d0.year} Fabrizio Bacchin</span>
    <nav class="piede__link etichetta">
      <a href="mailto:info@bacchin.app">info@bacchin.app</a>
      <a href="{casa}privacy">{t['privacy']}</a>
    </nav>
  </footer>

</div>
</body>
</html>
""", d0


def aggiorna_sitemap(d0):
    with open(SITEMAP, encoding="utf-8") as fh:
        s = fh.read()
    for lg in LINGUE:
        u = url(lg)
        voce = f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{d0.isoformat()}</lastmod>\n  </url>\n"
        if f"<loc>{u}</loc>" in s:
            s = re.sub(rf"  <url>\n    <loc>{re.escape(u)}</loc>\n    <lastmod>[^<]*</lastmod>\n  </url>\n", voce, s)
        else:
            s = s.replace("</urlset>", voce + "</urlset>")
    with open(SITEMAP, "w", encoding="utf-8") as fh:
        fh.write(s)


def main():
    eur, est = scarica("EURIBOR.csv"), scarica("ESTER.csv")
    for lg in LINGUE:
        testo, d0 = pagina(lg, eur, est)
        with open(os.path.join(QUI, "finanza", L[lg]["slug"] + ".html"), "w", encoding="utf-8") as fh:
            fh.write(testo)
    aggiorna_sitemap(d0)
    print(f"Euribor oggi in {len(LINGUE)} lingue: fixing del {d0.isoformat()}")


if __name__ == "__main__":
    main()
