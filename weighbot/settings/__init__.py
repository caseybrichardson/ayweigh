import os

from weighbot.settings.base import *

if os.environ.get("ENV_NAME") == 'production':
    from weighbot.settings.production import *
else:
    from weighbot.settings.local import *
