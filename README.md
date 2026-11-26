# bacchin.app: come si aggiorna il sito

Guida per le sessioni che lavorano sul sito, in particolare quando si aggiornano
le pagine di **assistenza** e di **privacy** delle app.

Stato verificato il 26 novembre 2026.

## La regola in una riga

Le pagine si modificano **solo** nel repo `fbacchin/fbacchin.github.io`.
Il repo `fbacchin/app` **non serve più**: GitHub lo ha bloccato il 25 novembre
2026. Da allora `https://fbacchin.github.io/app/...` è servito dalla cartella
`app/` di questo stesso repo, quindi risponde solo per i file che ci sono (le
pagine di assistenza e privacy, il manifest dei codici di gara) e dà 404 per
tutto il resto. I dati che le app scaricano escono da `bacchin.app` (vedi «Da
dove arrivano i dati»).

## Dove sta cosa

| Cosa | Repository | Si vede su | Si modifica? |
|---|---|---|---|
| Il sito: home, pagine delle app, assistenza, privacy | `fbacchin/fbacchin.github.io` | `https://bacchin.app` | **Sì, qui** |
| I dati letti dalle app (tassi, Gottardo) | Worker di Cloudflare, fuori dai repo | `https://bacchin.app/tassi/` e `https://widget.bacchin.app/` | No: non sono file del sito |
| Il vecchio repo dei dati (bloccato da GitHub dal 25 novembre 2026) | `fbacchin/app` | niente: `fbacchin.github.io/app/` ora mostra la cartella `app/` di questo repo | No: non si usa più |
| I giochi | `fbacchin/Giochi` | `https://giochi.bacchin.app` | Sì, nel loro repo |

### Come viene pubblicato il sito

`bacchin.app` è servito da **Cloudflare Pages**, che pubblica da solo il ramo
`main` di `fbacchin/fbacchin.github.io`. Ogni commit su `main` va online in
meno di un minuto: non c'è una fase di prova.

Cloudflare toglie `.html` dagli indirizzi con un reindirizzamento:
`/Leasing.html` diventa `/Leasing`, `/app/Leasing/support.html` diventa
`/app/Leasing/support`. Nei link interni e su App Store Connect usare la forma
**senza** `.html`.

## I file del sito (`fbacchin/fbacchin.github.io`)

```
index.html              home
stile.css               foglio di stile comune (richiamato come stile.css?v=...)
fonts/                  caratteri ospitati sul sito (niente Google Fonts)
privacy.html            privacy del sito + indice di assistenza e privacy delle app
EuriborX.html           pagine di presentazione, una per app
LiborX.html
Mortgage.html
Leasing.html
gotthard.html
Burraco.html
codici.html
perspecta.html
Regione.html
SwissCanton.html
USState.html
EuriborMac.html         solo un rimando a /EuriborX (app dismessa)
strumenti/euribor_oggi.py   lo script che genera Euribor oggi in 5 lingue
.github/workflows/euribor-oggi.yml   lo fa girare 4 volte al giorno
tennis/                 simulatore ranking ATP
finanza/                Euribor oggi in 5 lingue (euribor-oggi, -today, -aujourdhui,
                        -heute, -hoy: GENERATE, non modificare a mano), Stock Tracker e
                        Dashboard BCE (con chart.umd.min.js, Chart.js ospitato qui)
_redirects              rimandi di Cloudflare (per esempio /euribor-oggi -> /finanza/euribor-oggi)
stampa/                 materiali stampa di Gottardo Live
sitemap.xml  robots.txt  404.html  og.png
app-ads.txt             serve a Google AdMob: NON cancellare
app/                    assistenza e privacy di ogni app  <-- il lavoro si fa qui
en/ fr/ de/ es/         il sito tradotto (vedi «Il sito in 5 lingue»)
app-store-badge-*.svg   badge ufficiali Apple, uno per lingua (it, en, fr, de, es)
```

### Il sito in 5 lingue

L'italiano sta nella radice; inglese, francese, tedesco e spagnolo stanno in
`en/`, `fr/`, `de/`, `es/`, con gli **stessi nomi di file**: `EuriborX.html` →
`/en/EuriborX`, `finanza/stock-tracker.html` → `/fr/finanza/stock-tracker`.
Sono tradotte 16 pagine: home, le 11 pagine delle app, `privacy.html`,
`404.html`, Stock Tracker e Dashboard BCE. Restano a parte Euribor oggi (generata
in 5 lingue dallo script), il simulatore ATP (`tennis/`, italiano e inglese), i
materiali stampa e le pagine `app/` (già multilingua, scelgono la lingua del
browser).

- **Ogni pagina ha** i `<link rel="alternate" hreflang>` verso le 5 versioni (più
  `x-default` = italiano) e il selettore `<nav class="lingue-sito">` subito sotto
  la testata. Chi sceglie una lingua dal selettore la salva nel browser
  (`localStorage` `bacchin-lang`).
- **Solo la home italiana** porta alla lingua del browser alla prima visita (se è
  en, fr, de o es); una scelta fatta dal selettore vince sempre. I motori di
  ricerca non vengono reindirizzati.
- **Nelle pagine tradotte** i link interni puntano alla stessa lingua (`/en/...`),
  il foglio di stile è `/stile.css` (assoluto), il badge è
  `/app-store-badge-<lingua>.svg` e i link all'App Store usano lo storefront della
  lingua (`gb`, `fr`, `de`, `es`). Il badge francese è più largo: 152 px.
- **Se cambi una pagina italiana, cambia anche le 4 traduzioni.** Stessa struttura,
  stessi link (adattati alla lingua), solo il testo tradotto. Le pagine nuove vanno
  aggiunte in tutte e 5 le lingue, con hreflang e selettore, oltre che in `sitemap.xml`.
- Tedesco con la grafia svizzera (`ss`, mai `ß`), «du»; francese con «vous»;
  spagnolo con «tú». I nomi delle app non si traducono.

### La cartella `app/`: assistenza e privacy

Una cartella per app. Attenzione: i nomi dei file non sono uniformi.

| App | Cartella | Assistenza | Privacy |
|---|---|---|---|
| Euribor X | `app/EuriborX/` | `support.html` | `privacy.html` |
| Libor X | `app/LiborX/` | `support.html` | `privacy.html` |
| Mortgage Calculators | `app/Mortgage/` | `support.html` | `privacy.html` |
| Leasing Calculators | `app/Leasing/` | `support.html` | `privacy.html` |
| Gottardo Live | `app/gotthard/` | `support-gotthard.html` | `privacy-gotthard.html` |
| Burraco Score | `app/Burraco/` | `support-burraco.html` | `privacy-burraco.html` |
| Codice di Gara Burraco | `app/codici/` | `support-codicedigara.html` | `privacy-codicedigara.html` |
| Perspecta | `app/perspecta/` | `support-perspecta.html` | `privacy-perspecta.html` |
| Indovina la Regione | `app/Regione/` | `support-regione.html` | `privacy-regione.html` |
| Guess the Swiss Canton | `app/SwissCanton/` | `support-swisscanton.html` | `privacy-swisscanton.html` |
| Guess the US State | `app/USState/` | `support-usstate.html` | `privacy-usstate.html` |
| Health Companion (non pubblicata) | `app/healthcompanion/` | `support-healthcompanion.html` | `privacy-healthcompanion.html` |
| Valichi (non pubblicata) | `app/valichi/` | `support-valichi.html` | `privacy-valichi.html` |
| Volcano (non pubblicata) | `app/volcano/` | `support-volcano.html` | `privacy-volcano.html` |

L'indirizzo pubblico di ogni pagina è
`https://bacchin.app/app/<Cartella>/<file senza .html>`, per esempio
`https://bacchin.app/app/Leasing/support`.

## Da dove arrivano i dati

Il repo `fbacchin/app` è bloccato: le app e il sito non possono più leggerlo.
Le versioni delle app già distribuite che puntavano a `fbacchin.github.io/app/...`
non ricevono più i dati che stavano lì (tassi, Gottardo) finché non escono con
gli indirizzi nuovi.

**Già spostati**

- **Tassi** (`https://bacchin.app/tassi/`): `EURIBOR.csv`, `ESTER.csv`,
  `LIBOR-USD-SOFR.csv`, `LIBOR-GBP.csv`, `SARON-CHF.csv`, `TONAR-JPY.csv`. Li serve un
  Worker di Cloudflare, con cache di 15 minuti e copia di riserva. Stesso
  formato di prima: intestazione `"Date","Week day","ON","1W","1M","2M","3M","6M","12M"`,
  righe dalla più recente, data `gg.mm.aaaa`. Hanno `Access-Control-Allow-Origin: *`,
  quindi il browser può leggerli dal sito. La sicurezza della zona risponde 403
  allo user agent «Python-urllib»: gli script ne impostano uno proprio.
  - L'Euribor è quello di EMMI, ridistribuito dalla Deutsche Bundesbank con un
    giorno lavorativo di ritardo (la licenza lo richiede): il fixing di un giorno
    arriva nel corso del giorno lavorativo successivo. L'€STR arriva dalla BCE la
    mattina del giorno lavorativo successivo.
- **Gottardo** (`https://widget.bacchin.app/latest.json`, più `history.json` per
  le ultime 24 ore): un Worker di Cloudflare («gottardo-widget») che legge la
  funzione `gotthard` del server Back4App, la stessa dell'app, con cache di 3
  minuti. Il file `latest.json` ha `time`, `south` e `north` (con `km` e `wait`,
  `null` se non c'è coda) e `tunnel`. Ha il CORS aperto.
- **Codici di gara** (`/app/codici/manifest.json` e gli indici `fibur/` e
  `fitab/`): stanno in `app/codici/` di questo repo. Il manifest risponde anche
  all'indirizzo vecchio `https://fbacchin.github.io/app/codici/manifest.json`, quindi
  le app già distribuite funzionano. La home e `codici.html` lo leggono dallo
  stesso sito (`/app/codici/manifest.json`). **I PDF dei regolamenti ufficiali
  di FIBur e FITaB non vanno ospitati qui né linkati:** sono documenti di terzi
  e il loro hosting è il probabile motivo del blocco di `fbacchin/app`. Il
  manifest contiene ancora i campi `pdf.url`, che danno 404: le pagine del sito
  non li usano.

**Da verificare**

- **Valichi e Volcano:** i dati non sono letti dal sito, ma le app hanno ancora
  gli indirizzi vecchi (ADEV-796 e ADEV-797).

**Come si leggono dalle pagine del sito.** Tassi e Gottardo con l'indirizzo
completo (`https://bacchin.app/tassi/...` o `https://widget.bacchin.app/...`); il
manifest dei codici di gara con il percorso dello stesso sito.
Se il dato non arriva, la pagina mostra un messaggio generico («riprova più
tardi»).

**Burraco.** Gli ultimi due rimandi in `fbacchin/app` (`Burraco/privacy-burraco.html`
e `support-burraco.html`) non sono più raggiungibili con il repo bloccato:
Burraco Score 5.0.2, che apre già `bacchin.app`, è in vendita dal 13 ottobre
2026. Non serve altro (ADEV-776).

**Euribor oggi.** Le pagine `finanza/euribor-oggi` e le versioni nelle altre
lingue le genera `strumenti/euribor_oggi.py` dai CSV di `bacchin.app/tassi/`. Il
workflow `.github/workflows/euribor-oggi.yml` lo lancia alle 6:30, 10:30, 14:30 e
18:30 UTC.

## Procedura: aggiornare assistenza o privacy di un'app

1. **Parti dall'ultima versione.** Clona di nuovo
   `fbacchin/fbacchin.github.io`, oppure fai `git pull`. Più sessioni lavorano
   sullo stesso repo e `finanza/euribor-oggi.html` cambia da sola più volte al giorno:
   una copia vecchia sovrascrive il lavoro degli altri.
2. **Modifica solo i file dell'app** in `app/<Cartella>/`. Modifiche mirate:
   non riscrivere la pagina se cambia un paragrafo.
3. **Aggiorna la data** in cima alla pagina («Aggiornato al …»).
4. **Tutte le lingue.** Le pagine sono multilingua nello stesso file: la
   modifica va fatta in ogni lingua presente.
5. **Controlla le pagine collegate**: aggiornale solo se cambia qualcosa che
   dicono:
   - la pagina di presentazione dell'app nella radice (per esempio
     `Leasing.html`): sezione sul prezzo e sulla pubblicità, riga
     «Piattaforma», riga «Prezzo»;
   - la riga dell'app in `index.html`;
   - l'indice delle app in `privacy.html`, se cambia il nome dell'app o se
     l'app viene pubblicata o ritirata;
   - `sitemap.xml`: la data `lastmod` della pagina di presentazione toccata.
6. **Prima di pubblicare** fai `git fetch` e controlla che `main` non sia
   cambiato nel frattempo. Se è cambiato, riporta le tue modifiche sulla
   versione nuova.
7. **Pubblica** con un commit su `main`, con un messaggio che dica app e
   versione (esempio: `Leasing 3.1: supporto con Leasing Legacy`). Se la
   sessione non può scrivere sul repo, prepara uno zip con i soli file
   cambiati, con le cartelle al loro posto, da caricare a mano con
   «Add file → Upload files».
8. **Verifica online** dopo un minuto: apri l'indirizzo su `bacchin.app` e
   controlla che il testo nuovo ci sia.

## Aggiungere un'app nuova

1. Crea `app/<Cartella>/` con assistenza, privacy e icona.
2. Crea la pagina di presentazione nella radice, copiando la struttura di una
   esistente (per esempio `Leasing.html`).
3. Aggiungi la riga in `index.html`.
4. Aggiungi la riga nell'indice di `privacy.html`, **solo se l'app è
   pubblicata** sull'App Store.
5. Aggiungi la pagina di presentazione a `sitemap.xml`.
6. Sistema i link «precedente / successiva» in fondo alle pagine delle app
   vicine.
7. Su App Store Connect usa gli indirizzi `https://bacchin.app/app/...`.
   Per un'app nuova non si usa `fbacchin/app`.

## Ritirare un'app

Togli la riga da `index.html`, da `privacy.html` e da `sitemap.xml`, poi sistema
i link delle app vicine. La pagina di presentazione diventa un rimando (come
`EuriborMac.html`). Assistenza e privacy in `app/<Cartella>/` **restano**:
servono a chi ha ancora l'app installata.

## Convenzioni da rispettare

- **Caratteri:** si usa `/fonts/fonts.css`. Nessun link a Google Fonts.
- **Lingue:** ogni pagina del sito esiste in 5 lingue (vedi «Il sito in 5
  lingue»): una modifica fatta solo in italiano lascia le traduzioni indietro.
- **Piede delle pagine del sito:** indirizzo email e link «Privacy e
  assistenza» verso `/privacy`.
- **Email:** le pagine del sito usano `info@bacchin.app`. Le pagine di
  assistenza e privacy delle app usano `bacchin@tiscali.it`: è voluto, non
  uniformare.
- **Link ad assistenza e privacy** dalle pagine del sito: forma breve, per
  esempio `/app/Leasing/support`.
- **Link all'App Store:** ogni pagina di presentazione ha sotto il titolo il
  badge ufficiale Apple (`app-store-badge-it.svg`, scaricato da Apple: non va
  ridisegnato, ricolorato né deformato; altezza minima 40px) e la riga
  «App Store» nella scheda in fondo. L'indirizzo è quello completo della
  scheda, `https://apps.apple.com/it/app/<nome>/id<numero>`. Perspecta non ce
  l'ha finché non è sull'App Store.
- **Dati in diretta:** le pagine del sito leggono i dati con l'indirizzo
  completo `https://bacchin.app/tassi/...` o `https://widget.bacchin.app/...`.
  Fa eccezione il manifest dei codici di gara, che sta nel sito e si legge con
  `/app/codici/manifest.json`.
- **Modello di vendita attuale** di Euribor X, Libor X, Mortgage e Leasing:
  una sola app gratuita con pubblicità, che si toglie con abbonamento annuale
  o acquisto una tantum. La vecchia versione a pagamento si chiama «Legacy» e
  non riceve aggiornamenti. Non esistono più versioni «Light» di queste app.
- **Euribor per Mac** è dismessa e tolta dall'App Store: le sue pagine di
  assistenza e privacy sono state cancellate. Resta solo `EuriborMac.html`, che
  rimanda a /EuriborX.
- **Guess the China Province** è stata ritirata dalla vendita (ottobre 2026):
  era l'ultima app che usava `Help.html` e il repo `privacy-and-support`,
  entrambi cancellati.

## Cose da non fare

- Non usare `fbacchin/app`: è bloccato da GitHub, niente di nuovo va messo lì e
  nessuna pagina deve puntarci.
- Non cambiare i nomi dei file CSV in `bacchin.app/tassi/`: le app già
  distribuite li leggono con quel nome.
- Non modificare `finanza/euribor-oggi.html` a mano: la modifica dura poche ore. Si
  cambia `strumenti/euribor_oggi.py`, poi anche la pagina.
- Non cancellare `app-ads.txt`.
- Non aggiungere a `privacy.html` le app non pubblicate (Health Companion,
  Valichi, Volcano).
- Non ricostruire un file partendo da una copia vecchia.

## Ancora da fare

- Inserire nelle pagine delle app delle immagini con le funzionalità
  descritte nel testo.

## Controllo finale

- [ ] Ho lavorato sull'ultima versione di `main`.
- [ ] Ho modificato solo `fbacchin/fbacchin.github.io` (niente `fbacchin/app`).
- [ ] La data «Aggiornato al» è quella di oggi.
- [ ] Tutte le lingue della pagina sono allineate.
- [ ] Pagina di presentazione, home, indice privacy e sitemap dicono la stessa
      cosa.
- [ ] La pagina si apre su `https://bacchin.app/app/<Cartella>/<file>`.
