# Test End-to-End con Playwright - POCKET-ZENA

I test E2E verificano il comportamento dell'applicazione dal punto di vista dell'utente, simulando interazioni reali sul browser. Vengono eseguiti con **Playwright** contro il backend FastAPI in esecuzione locale.

## Struttura

```
tests/e2e/
├── helpers.js            # Funzioni condivise (login, createDuel, addZenamon, ...)
├── login.spec.js         # Flusso di login e validazione nickname
├── duel.spec.js          # Creazione e accesso alle stanze di duello
├── team_selection.spec.js # Selezione squadra (ricerca, aggiunta, conferma)
├── battle.spec.js        # Flusso di battaglia (turni, cambio Zenamon)
└── spectator.spec.js     # Modalità spettatore e reazioni emoji
```

## Prerequisiti

- **Node.js** >= 18
- **Python** con l'ambiente virtuale del progetto attivo
- Il backend deve poter avviarsi su `localhost:8000`

## Installazione

```bash
npm install
npx playwright install chromium
```

## Esecuzione

```bash
# Tutti i test (avvia il backend automaticamente)
npm run test:e2e

# Con interfaccia grafica Playwright
npm run test:e2e:ui

# In modalità headed (browser visibile)
npm run test:e2e:headed

# Apre il report HTML dell'ultima esecuzione
npm run test:e2e:report
```

Se il backend è già in esecuzione su porta 8000, Playwright lo riusa automaticamente (comportamento controllato da `reuseExistingServer` in `playwright.config.js`).

## Copertura dei Test

### `login.spec.js`
| Test | Cosa verifica |
|------|---------------|
| Nickname valido | Transizione login → menu, nickname mostrato in maiuscolo |
| Nickname < 3 caratteri | Alert con messaggio esplicativo, rimane su login |
| Campo vuoto | Alert, rimane su login |
| Nickname in minuscolo | Viene convertito automaticamente in maiuscolo |

### `duel.spec.js`
| Test | Cosa verifica |
|------|---------------|
| Crea duello | Codice a 4 caratteri alfanumerici in lobby |
| Join codice inesistente | Alert di errore, rimane su menu |
| Join senza codice | Alert |
| Join valido (P2) | P2 arriva alla selezione squadra |
| Polling P1 | P1 viene portato alla selezione quando P2 entra |

### `team_selection.spec.js`
| Test | Cosa verifica |
|------|---------------|
| Ricerca per nome | Lista risultati visibile |
| Ricerca per ID numerico | Risultato corretto (es. 25 → Pikachu) |
| Aggiunta Zenamon | Contatore squadra aggiornato |
| < 3 Zenamon | Bottone "Conferma" nascosto |
| 3 Zenamon | Bottone "Conferma" visibile |
| Zenamon duplicato | Non viene aggiunto due volte |

### `battle.spec.js`
| Test | Cosa verifica |
|------|---------------|
| Raggiungimento battaglia | Entrambi i giocatori vedono la battle page |
| Nomi Zenamon | I nomi degli attivi sono visibili (non `???`) |
| Griglia mosse | I pulsanti delle mosse sono presenti |
| Invio attacco | Appare il messaggio "In attesa avversario" |
| Turno completo | Il log di battaglia si popola dopo la risoluzione |
| Menu cambio | Mostra i 3 slot della squadra |
| Cambio pre-turno | Dopo la selezione del nuovo Zenamon le sue mosse appaiono (fix bug switch) |

### `spectator.spec.js`
| Test | Cosa verifica |
|------|---------------|
| Accesso come spettatore | Battle page visibile |
| Controlli nascosti | I bottoni di attacco non sono visibili |
| Vista in tempo reale | Gli HP si aggiornano quando la battaglia inizia |
| Reazione emoji | Il bottone è cliccabile senza errori |

## Note Tecniche

### Isolamento dei Test
I test usano nickname generati da timestamp (`uniqueNick()`) per evitare collisioni nel database SQLite condiviso. Ogni suite di test lavora su dati propri senza necessità di reset del DB tra un'esecuzione e l'altra.

### Scenari Multiplayer
I test che coinvolgono due o tre giocatori usano `browser.newContext()` di Playwright per creare contesti browser completamente isolati (cookie, localStorage, sessione separati), che simulano utenti indipendenti.

### Dipendenza da PokeAPI
Le ricerche di Zenamon fanno chiamate reali a `pokeapi.co` la prima volta (dati poi in cache locale SQLite). In ambienti CI senza accesso a internet, pre-popolare la cache o usare un mock HTTP è necessario.

### Polling
L'app aggiorna lo stato ogni 2 secondi. I test che attendono transizioni di stato (es. lobby → selezione, selezione → battaglia) usano `waitForSelector` con timeout di 10-15 secondi per assorbire un paio di cicli di polling.

## Aggiungere Nuovi Test

1. Creare un file `tests/e2e/<nome>.spec.js`
2. Importare gli helper condivisi da `./helpers`
3. Per test multiplayer, usare `browser.newContext()` e chiudere i contesti nel blocco `finally`

```js
const { test, expect } = require('@playwright/test');
const { uniqueNick, login } = require('./helpers');

test('esempio', async ({ page }) => {
  await login(page, uniqueNick());
  await expect(page.locator('#menu-page')).toBeVisible();
});
```
