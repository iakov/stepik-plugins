import logging
import logging.config
import os
import sys

import structlog

from datetime import timedelta

from . import log


PACKAGE_ROOT = os.path.dirname(os.path.dirname(__file__))
DEBUG = False

RPC_TRANSPORT_URL = 'rabbit://guest:guest@localhost:5672//'

# use current user to execute `sandboxed` code.
SANDBOX_USER = None
SANDBOX_FOLDER = os.path.join(PACKAGE_ROOT, 'sandbox')
SANDBOX_PYTHON = os.path.join(SANDBOX_FOLDER, 'python', 'bin', 'python3')
SANDBOX_JAVA = None
SANDBOX_ENV = {
    'LANG': 'en_US.UTF-8',
}
ARENA_DIR = os.path.join(PACKAGE_ROOT, 'arena')

MB = 1024 * 1024
JAVA_RESERVED_MEMORY = 400 * MB

SANDBOX_LIMITS = {
    'TIME': 60,
    'MEMORY': 256 * MB,
    'CAN_FORK': False,
    'FILE_SIZE': 0
}

COMPILERS = {

}

INTERPRETERS = {

}

COMPILER_LIMITS = {
    'TIME': 60,
    'MEMORY': 512 * MB,
    'CAN_FORK': True,
    'FILE_SIZE': 256 * MB
}

USER_CODE_LIMITS = {
    'TIME': 10,
    'MEMORY': 512 * MB,
    'CAN_FORK': False,
    'FILE_SIZE': 0
}

DATASET_QUIZ_TIME_LIMIT = timedelta(minutes=5)
DATASET_QUIZ_SIZE_LIMIT = 10 * MB

# These quizzes will be scored in edy in a separate celery queue.
COMPUTATIONALLY_HARD_QUIZZES = ['admin', 'code', 'dataset']

ROOTNROLL_API_URL = ''
ROOTNROLL_USERNAME = ''
ROOTNROLL_PASSWORD = ''

LOGGING_JSON = False
LOGGING_SENTRY = False

try:
    from .local_settings import *
except ImportError:
    pass
try:
    # If stepic-plugins rpc server runs in fake mode in scope of edy project
    # (see PLUGINS_RPC_FAKE_SERVER setting) try to import local settings for
    # plugins from edy.
    from edy.plugins_local_settings import *
except ImportError:
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] [%(name)s] %(levelname)s %(message)s'
        },
        'structlog_json': {
            '()': 'stepic_plugins.log.LoggingJsonFormatter',
            'format': '%(message)s'
        }
    },
    'filters': {
        'require_logging_json_true': {
            '()': 'stepic_plugins.log.RequireLoggingJsonTrue'
        },
        'require_logging_json_false': {
            '()': 'stepic_plugins.log.RequireLoggingJsonFalse'
        },
        'require_logging_sentry_true': {
            '()': 'stepic_plugins.log.RequireLoggingSentryTrue'
        },
    },
    'handlers': {
        # TODO: configure sentry
        #'sentry': {
        #    'level': 'WARNING',
        #    'filters': ['require_logging_sentry_true'],
        #    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        #},
        'console': {
            'level': 'DEBUG',
            'filters': ['require_logging_json_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_json': {
            'level': 'DEBUG',
            'filters': ['require_logging_json_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'structlog_json',
        },
    },
    'loggers': {
        'py.warnings': {
            'handlers': ['console'],
            'propagate': False,
        },
        'stepic_plugins': {
            'handlers': ['console', 'console_json'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'console_json'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

logging.config.dictConfig(LOGGING)
logging.captureWarnings(True)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        log.add_supervisor_instance_id,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer() if LOGGING_JSON else
        structlog.processors.KeyValueRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

from .utils import configure_jail_code
configure_jail_code(sys.modules[__name__])
