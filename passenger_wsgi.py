import sys
import os

# Aggiungi la cartella del progetto al path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from a2wsgi import ASGIMiddleware
from backend.main import app

# L'oggetto 'application' è quello cercato da PythonAnywhere
application = ASGIMiddleware(app)
