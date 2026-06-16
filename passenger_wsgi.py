import sys
import os
import logging

# Configura il logging per vedere gli errori nel file log di PythonAnywhere
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aggiungi la cartella del progetto al path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

try:
    from a2wsgi import ASGIMiddleware
    from backend.main import app
    # L'oggetto 'application' è quello cercato da PythonAnywhere
    application = ASGIMiddleware(app)
    logger.info("Applicazione POCKET-ZENA caricata correttamente.")
except Exception as e:
    logger.error(f"ERRORE CRITICO durante il caricamento dell'applicazione: {e}")
    # Rialziamo l'eccezione per far sì che Passenger la registri nei log
    raise
