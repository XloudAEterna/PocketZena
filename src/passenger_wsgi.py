import sys
import os
import logging
import time

start_load = time.time()

# Configura il logging per vedere gli errori nel file log di PythonAnywhere
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aggiungi la cartella del progetto al path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

try:
    from a2wsgi import ASGIMiddleware
    from src.backend.main import app
    from src.backend.models.database import init_db
    
    # Forza l'inizializzazione del DB per ambienti WSGI dove il lifespan di FastAPI potrebbe non essere triggerato
    logger.info("Inizializzazione database via WSGI...")
    init_db()
    
    # Evitiamo doppia inizializzazione se il lifespan venisse comunque chiamato
    os.environ["SKIP_DB_INIT"] = "1"
    
    # L'oggetto 'application' è quello cercato da PythonAnywhere
    application = ASGIMiddleware(app)
    logger.info(f"Applicazione POCKET-ZENA caricata correttamente in {time.time() - start_load:.2f} secondi.")
except Exception as e:
    logger.error(f"ERRORE CRITICO durante il caricamento dell'applicazione: {e}")
    # Rialziamo l'eccezione per far sì che Passenger la registri nei log
    raise
