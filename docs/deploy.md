# Guida al Deploy - POCKET-ZENA

Questa guida spiega come distribuire il progetto **POCKET-ZENA** utilizzando **PythonAnywhere** per il backend e **GitHub Pages** per il frontend.

## 1. Backend (PythonAnywhere)

PythonAnywhere è ideale per questo progetto perché offre un filesystem persistente per il database SQLite.

### Passaggi:
1. **Crea un account**: Registrati su [pythonanywhere.com](https://www.pythonanywhere.com).
2. **Apri una Console Bash**:
   - Clona il tuo repository:
     ```bash
     git clone https://github.com/TUO-UTENTE/aiproj.git
     ```
   - Vai nella cartella del progetto:
     ```bash
     cd aiproj
     ```
   - Crea un Virtual Environment:
     ```bash
     mkvirtualenv --python=/usr/bin/python3.10 venv  # O la versione desiderata
     pip install -r requirements.txt
     ```
3. **Configura la Web App**:
   - Vai nella sezione **Web** della dashboard di PythonAnywhere.
   - Clicca su **Add a new web app**.
   - Scegli **Manual Configuration** (non Django/Flask/etc.) e seleziona la versione di Python usata nel venv.
   - **Virtualenv**: Inserisci il percorso del venv creato (es: `/home/TUO-UTENTE/.virtualenvs/venv`).
   - **Code**: Inserisci il percorso del progetto (es: `/home/TUO-UTENTE/aiproj`).
   - **WSGI configuration file**: Clicca sul link al file e sostituisci il contenuto con quello di `passenger_wsgi.py` presente nel repository.
4. **Database**:
   - Il database `pocket_zena.sqlite3` verrà creato automaticamente nella cartella root al primo avvio.

## 2. Frontend (GitHub Pages)

Il frontend viene distribuito automaticamente tramite GitHub Actions.

### Passaggi:
1. **Abilita GitHub Pages**:
   - Vai nelle **Settings** del tuo repository su GitHub.
   - Vai in **Pages**.
   - Sotto **Build and deployment**, imposta la sorgente su **GitHub Actions** (oppure lascia che l'action crei il branch `gh-pages` e seleziona quello).
2. **Configura l'URL dell'API**:
   - Prima di fare il deploy, apri `frontend/js/app.js`.
   - Modifica `API_BASE` per puntare al tuo indirizzo PythonAnywhere:
     ```javascript
     const API_BASE = 'https://TUO-UTENTE.pythonanywhere.com/api/v1';
     ```

## 3. Pipeline CI/CD

Il progetto include due workflow in `.github/workflows`:
- **CI - Test**: Esegue i test automatizzati ad ogni push su `main`.
- **Deploy Frontend**: Esegue il deploy della cartella `frontend/` su GitHub Pages quando ci sono modifiche in quella cartella.

## Note sulla Sicurezza
- Assicurati che `pocket_zena.sqlite3` sia nel tuo `.gitignore` per evitare di sovrascrivere il database di produzione con quello di sviluppo.
