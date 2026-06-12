# Opzioni di Hosting per Backend Python

Per il progetto **POCKET-ZENA**, il servizio di hosting deve supportare Python. Avendo rimosso il requisito dei WebSockets in favore di una comunicazione HTTP standard (Polling/SSE), le opzioni diventano più flessibili.

## 1. PythonAnywhere (Ottimo per semplicità e SQLite)
- **Vantaggi**:
    - Specializzato esclusivamente in Python.
    - Piano gratuito molto stabile e facile da configurare.
    - **Persistenza**: Offre uno storage su disco persistente, permettendo l'uso di **SQLite** senza perdere dati al riavvio.
    - **Database integrato**: Offre 1 database MySQL gratuito.
- **Sito**: [pythonanywhere.com](https://www.pythonanywhere.com)

## 2. Render
- **Vantaggi**:
    - Ottimo piano gratuito (Free Tier).
    - Distribuzione automatica da GitHub.
    - **Database integrato**: Offre **PostgreSQL** gratuito (scadenza 90 giorni).
- **Svantaggi**:
    - Nel piano gratuito, l'istanza va in "sleep" dopo 15 minuti di inattività.
    - **Filesystem effimero**: I file salvati localmente (come un DB SQLite) vengono cancellati a ogni riavvio/sleep.
- **Sito**: [render.com](https://render.com)

## 3. Koyeb
- **Vantaggi**:
    - Piano gratuito ("Nano") che non va in sleep.
    - Molto veloce nel deploy.
- **Svantaggi**:
    - **Nessun Database integrato gratuito**: Richiede di collegare un servizio esterno per la persistenza.
    - **Filesystem effimero**: Non permette l'uso di SQLite persistente.
- **Sito**: [koyeb.com](https://koyeb.com)

## 4. Railway
- **Vantaggi**:
    - Estrema facilità d'uso.
    - Offre database PostgreSQL/MySQL con trial iniziale.
- **Sito**: [railway.app](https://railway.app)

---

### Decisione Finale
È stato scelto lo **Scenario "Tutto in uno" (Minimal)**:
- **Hosting Backend**: **PythonAnywhere**
- **Database**: **SQLite**
- **Motivazione**: Semplicità di configurazione, persistenza dei dati garantita su filesystem e tutto gestito in un unico account gratuito.
