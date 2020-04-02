import os
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '!o)2tl!fqbytg6(@1tc-(nac2!s^smw)amvy^#tos%utjkhpt^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '159.65.66.59', 'fuelfinderzim.com',]

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    '159.65.66.59',
    # ...
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'application.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Application definition

INSTALLED_APPS = [
    'national.apps.NationalConfig',
    'fuelUpdates.apps.FuelupdatesConfig',
    'buyer.apps.BuyerConfig',
    'company.apps.CompanyConfig',
    'serviceStation.apps.ServicestationConfig',
    'zeraPortal.apps.ZeraportalConfig',
    'supplier.apps.SupplierConfig',
    'accounts.apps.AccountsConfig',
    'noic.apps.NoicConfig',
    'noicDepot.apps.NoicdepotConfig',
    'finder.apps.FinderConfig',
    'notification.apps.NotificationConfig',
    'whatsapp.apps.WhatsappConfig',
    'api.apps.ApiConfig',
    'users.apps.UsersConfig',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'mathfilters',
    'debug_toolbar',
    'comments.apps.CommentsConfig',
    'session_security',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'session_security.middleware.SessionSecurityMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'fuelfinder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'supplier.forms.fuelupdate',
                'supplier.forms.create_sub',
                'users.forms.approve_staf',
                'supplier.forms.fuelupdating1',
                'supplier.forms.fuelupdating2',
                'supplier.forms.stock_form',
                'supplier.forms.makeoffer',
            ],
        },
    },
]

WSGI_APPLICATION = 'fuelfinder.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fuel',
        'USER': 'fuel',
        'PASSWORD': '12345#',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'intelliwhatsappbanking@gmail.com'
EMAIL_HOST_PASSWORD = 'intelliafrica2019'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

DEFAULT_FROM_EMAIL = 'Fuel Finder Accounts <tests@marlvinzw.me>'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
AUTH_USER_MODEL = 'buyer.User'

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Harare'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

LOGIN_URL = 'login'

# update these in seconds seconds
SESSION_SECURITY_WARN_AFTER = 30
SESSION_SECURITY_EXPIRE_AFTER = 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
