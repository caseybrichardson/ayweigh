
from pathlib import Path

SECRET_KEY = '=uovxz)+s_9965719g^t*mpa7p&yjy)+h0kcnysp@qv0ujubjy'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
