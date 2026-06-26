# Changelog

Tutti i cambiamenti significativi a questo progetto saranno documentati in questo file.

### Aggiunto
- Supporto alla scelta della mossa nello stesso turno in cui si effettua uno switch dello Zenamon.
- Gestione del pareggio nel duello se entrambi i giocatori esauriscono i mostriciattoli nello stesso turno.
- Visualizzazione dello **sprite retro (back-sprite)** per il mostriciattolo del giocatore locale, per simulare la prospettiva classica dei giochi tascabili.
- Supporto completo per la modalità **Spettatore** nel frontend, inclusa la corretta gestione della visualizzazione e delle reazioni emoji con cooldown di 5 secondi.
- Supporto alla **ricerca parziale degli Zenamon** con visualizzazione di almeno 10 risultati.
- Animazioni CSS `pulse-damage` e `float-up` per feedback visivo durante il duello.
- Visualizzazione HP (attuale/massimo) nella schermata di switch.
- Configurazione della pipeline CI/CD tramite GitHub Actions (`.github/workflows/`).
- Workflow per test automatizzati via GitHub Actions.
- Adattatore WSGI `passenger_wsgi.py` per il supporto a PythonAnywhere.
- Guida dettagliata al deploy in `docs/deploy.md`.
- Manuale di gioco per l'utente finale in `docs/manuale.md`.

### Rimosso
- Supporto al deploy su GitHub Pages: il progetto ora utilizza esclusivamente PythonAnywhere per servire sia il frontend che il backend.
- Configurazione CORS wildcard (`*`) nel backend: rimosso il supporto a origini esterne per migliorare la sicurezza.

### Corretto
- Risolto errore CORS e configurazione dinamica API: implementato il rilevamento automatico dell'URL backend in `frontend/js/app.js` (usando percorsi relativi quando possibile) per garantire il corretto funzionamento sia in locale che in produzione.
- Risolto errore 504 Gateway Timeout su PythonAnywhere: migrata l'inizializzazione del database (`init_db`) al gestore di eventi `lifespan` di FastAPI (sostituendo il deprecato `@app.on_event("startup")`), garantendo un avvio più robusto e conforme alle ultime versioni del framework.
- Aggiunto endpoint `/api/v1/health` per il monitoraggio dello stato del servizio.
- Migliorato il logging dei tempi di caricamento in `passenger_wsgi.py` e `backend/main.py`.
- Risolto errore 500 su PythonAnywhere: implementato il calcolo del percorso assoluto per il database SQLite in `backend/models/database.py`, evitando crash dovuti a directory di lavoro errate.
- Risolti errori "HARAKIRI" (timeout) su PythonAnywhere:
    - Aggiunto `busy_timeout` a SQLite per gestire la concorrenza.
    - Introdotto caching persistente della lista Zenamon in `zenamon_names.json`.
    - Ottimizzato il recupero dei dati da PokeAPI con timeout stringenti e parallelismo migliorato.
- Migliorata la robustezza CORS: aggiunto un gestore di eccezioni globale in `backend/main.py` per garantire che anche gli errori 500 restituiscano header CORS validi.
- Aggiunto logging in `passenger_wsgi.py` per facilitare il debug degli errori di avvio sul server di produzione.
- Risolto errore CORS nel backend: configurato `allow_credentials=False` per permettere l'uso del wildcard `allow_origins=["*"]`, necessario per le chiamate da domini diversi (es. GitHub Pages).
- Corretti i permessi della GitHub Action per il deploy del frontend (aggiunto `contents: write`), risolvendo l'errore `exit code 128`.
- Implementato l'obbligo di switch per lo Zenamon esausto: il giocatore non può attaccare finché non cambia il mostriciattolo attivo.
- Risolto errore `sqlalchemy.exc.ArgumentError` durante lo switch del mostriciattolo per il secondo giocatore, causato da un'errata precedenza degli operatori nella query del database.
- Risolto errore `NameError: asyncio` e bug di definizione Pydantic (`Optional`) nell'endpoint di ricerca Zenamon parziale.
- Migliorato il feedback visivo nel frontend durante la ricerca: ora viene mostrato un messaggio di errore specifico in caso di problemi tecnici del server invece del generico "Nessun Zenamon trovato".
- Risolto errore 400 Bad Request nelle operazioni POST del frontend tramite l'introduzione di una gestione errori più robusta e messaggi di feedback all'utente.
- Allentati i vincoli del nickname nel backend (ora accetta lettere e numeri, lunghezza 3-10) per evitare errori di validazione inaspettati.
- Aggiunta validazione e feedback visivo nel frontend per la fase di login, ricerca Zenamon e invio azioni di battaglia.
- Risolto errore 404 nell'accesso al frontend tramite `/frontend/index.html`.
- Eliminato conflitto tra rotta API root e caricamento statici.
- **Risolto bug ricerca Zenamon**: Aggiunta colonna `moves` mancante nel database SQLite e ottimizzato il client PokeAPI per una ricerca più veloce e robusta.

### [Iniziale] - 2026-06-12
### Aggiunto
- Analisi iniziale dei requisiti basata su README.md e idee.md.
- Creato file TASKS.md con la lista delle attività previste.
- Ricerca sui servizi di hosting Python documentata in `docs/hosting.md`, estesa con l'analisi dei database gratuiti.
- Definizione delle meccaniche di gioco (3 mostriciattoli, PokeAPI, sistema classico) in `docs/meccaniche.md`.
- Aggiornato TASKS.md con le nuove specifiche confermate dall'utente.
- Confermato l'utilizzo di **FastAPI** come framework backend.
- Scelto **PythonAnywhere** per l'hosting e **SQLite** come database.
- Definizione del modello dati relazionale in `docs/modello-dati.md`.
- Definizione dettagliata della logica di combattimento in `docs/logica-combattimento.md`.
- Sketch e mockup descrittivo dell'interfaccia utente in `docs/mockup-interfaccia.md`.
- Definizione degli endpoint API REST e logica di polling in `docs/api-endpoints.md`.
- Inizializzazione repository Git e configurazione `.gitignore`.
- Configurazione ambiente di sviluppo Python (FastAPI, SQLAlchemy, Pytest).
- Creazione struttura cartelle per il frontend Vanilla JS.
- Implementazione dei modelli SQLAlchemy in `backend/models/database.py`.
- Implementazione del client PokeAPI con caching in `backend/pokeapi_client.py`.
- Creazione di unit test dettagliati per il client PokeAPI in `tests/test_pokeapi_client.py`.
- Verifica del corretto funzionamento del client tramite script di integrazione.
- Aggiunta la dipendenza `pytest-asyncio` in `requirements.txt` per supportare i test asincroni.
- Implementazione completa del backend e del frontend per il progetto **POCKET-ZENA**.
- Sviluppo di un motore di combattimento a turni simultanei con calcolo danni basato sulle statistiche ufficiali.
- Realizzazione di un'interfaccia utente Vanilla JS reattiva che supporta duelli in tempo reale tramite polling.
- Implementazione di unit test dedicati per il motore di combattimento (`tests/test_battle_engine.py`).
- Risolti problemi di sincronizzazione del database nei calcoli di fine duello tramite `db.flush()`.

### Modificato
- Configurato l'URL di produzione del backend (`API_BASE`) in `frontend/js/app.js` per puntare a PythonAnywhere.
- Aggiornato `docs/deploy.md` con l'URL reale del progetto.
- Aggiornato `requirements.txt` con la dipendenza `a2wsgi`.
- Aggiornato `README.md` con link alla documentazione e istruzioni per il deploy.
- Sincronizzato `TASKS.md` con lo stato finale del progetto.
- Rimosso l'utilizzo dei WebSockets in favore di HTTP standard (Polling/SSE).
- Aggiornate le opzioni di hosting in `docs/hosting.md` includendo PythonAnywhere.
- **Bonifica Nomenclatura**: Sostituiti tutti i riferimenti a marchi registrati (es. "Pokemon") con termini generici ("Zenamon", "mostriciattoli") per conformità legale.
