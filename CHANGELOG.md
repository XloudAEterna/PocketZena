# Changelog

Tutti i cambiamenti significativi a questo progetto saranno documentati in questo file.

### Aggiunto
- Configurazione della pipeline CI/CD tramite GitHub Actions (`.github/workflows/`).
- Workflow per test automatizzati e deploy automatico del frontend su GitHub Pages.
- Adattatore WSGI `passenger_wsgi.py` per il supporto a PythonAnywhere.
- Guida dettagliata al deploy in `docs/deploy.md`.
- Manuale di gioco per l'utente finale in `docs/manuale.md`.

### Corretto
- Risolto errore 404 nell'accesso al frontend tramite `/frontend/index.html`.
- Eliminato conflitto tra rotta API root e caricamento statici.

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
- Aggiornato `requirements.txt` con la dipendenza `a2wsgi`.
- Aggiornato `README.md` con link alla documentazione e istruzioni per il deploy.
- Sincronizzato `TASKS.md` con lo stato finale del progetto.
- Rimosso l'utilizzo dei WebSockets in favore di HTTP standard (Polling/SSE).
- Aggiornate le opzioni di hosting in `docs/hosting.md` includendo PythonAnywhere.
- **Bonifica Nomenclatura**: Sostituiti tutti i riferimenti a marchi registrati (es. "Pokemon") con termini generici ("Zenamon", "mostriciattoli") per conformità legale.
