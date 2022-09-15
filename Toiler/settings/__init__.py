import os
import dotenv

IS_LOCAL_AREA = os.getenv('LOCAL_AREA', False)

dotenv.load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                 'development.env' if IS_LOCAL_AREA else 'production.env')
)
from .base import *

try:
    if IS_LOCAL_AREA:
        from .development import *
        # INSTALLED_APPS.append('debug_toolbar')
        # MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        live = False
    else:
        live = True

except ImportError:
    live = True

if live:
    from .production import *
