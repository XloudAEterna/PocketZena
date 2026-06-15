# Lista Attività (TASKS.md) - Progetto POCKET-ZENA

## 1. Analisi e Progettazione
- [x] Definizione dettagliata della logica di combattimento (Sistema Classico: Tipi, Debolezze, Calcolo Danni)
- [x] Definizione del modello dati (Zenamon, Giocatore, Duello, Turno)
- [x] Conferma framework backend (FastAPI) e librerie per comunicazione (HTTP/Polling)
- [x] Sketch/Mockup dell'interfaccia utente (basato su idea-interfaccia.png)
- [x] Definizione degli endpoint API (REST) e della logica di polling/SSE
- [x] Ricerca e analisi database dei servizi di hosting (Render, PythonAnywhere, Koyeb)
- [x] Scelta finale hosting e database (Scenario SQLite)

## 2. Configurazione Ambiente
- [x] Inizializzazione repository Git
- [x] Setup ambiente virtuale Python e installazione dipendenze
- [x] Configurazione ambiente frontend (struttura cartelle vanilla JS)
- [x] Configurazione framework di test (pytest)

## 3. Sviluppo Backend (Python)
- [x] Implementazione client per PokeAPI (Nome, Immagine, Tipo) con sistema di caching
- [x] Unit test e verifica del client PokeAPI
- [x] Gestione delle "Stanze" di duello (creazione, accesso tramite codice - solo Multiplayer)
- [x] Implementazione logica dei turni (Fase 1: Scelta, Fase 2: Scontro)
- [x] Motore di calcolo danni e gestione stato mostriciattoli (3 per giocatore)
- [x] Sistema di aggiornamento via HTTP (Polling o Server-Sent Events)
- [x] Gestione spettatori e reazioni (Emoji classiche)

## 4. Sviluppo Frontend (Vanilla JS)
- [x] Schermata di Login (Nickname 3 caratteri)
- [x] Menu principale (Crea/Entra in duello)
- [x] Interfaccia di selezione mostriciattoli (Ricerca libera via PokeAPI)
- [x] Interfaccia di combattimento (Board, Animazioni base, Log)
- [x] Interfaccia spettatore (Vista passiva + Reazioni con emoji)

## 5. Test e Validazione
- [x] Unit test per la logica di combattimento
- [x] Test di integrazione per il flusso del duello
- [x] Bug fixing e rifiniture

## 6. Deploy
- [x] Configurazione della pipeline di CI/CD
- [x] Deploy del backend sul servizio scelto (Documentato in deploy.md)
- [x] Deploy del frontend (es. GitHub Pages o Vercel)

## 7. Documentazione
- [x] Aggiornamento README.md con istruzioni di installazione e avvio
- [x] Creazione manuale di gioco (regole di combattimento)
