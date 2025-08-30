import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from api import app

def handler(request):
    return app(request.environ, lambda status, headers: None)