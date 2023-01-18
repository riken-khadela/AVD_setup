import unittest
import os
import django

from log import Log
from utils import set_log
from conf import PRJ_PATH
from conf import LOG_LEVEL, LOG_DIR, LOG_IN_ONE_FILE

# setup django settings
from django.conf import settings
if not os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surviral_avd.settings')
django.setup()

from twbot.utils import get_random_password
from twbot.utils import get_real_random_password

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestPassword(unittest.TestCase):

    def test_get_random_password(self):
        pw = get_random_password()
        LOGGER.info(f'Random password: {pw}')
        self.assertNotEqual(pw, '')

    def test_get_real_random_password(self):
        pw = get_real_random_password()
        LOGGER.info(f'Random password: {pw}')
        self.assertNotEqual(pw, '')

