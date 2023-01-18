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

from twbot.utils import get_twitter_number, get_twitter_sms, get_summary
from twbot.utils import get_mobile_list

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestPhone(unittest.TestCase):

    def test_get_phone_number(self):
        number = get_twitter_number()
        LOGGER.info(f'Phone number: {number}')
        self.assertNotEqual(number, '')

    def test_get_sms(self):
        number = '18044530062'
        number = '19013520566'
        number = '15033893369'
        number = '15033893369'
        number = '17204665145'
        sms = get_twitter_sms(number)
        LOGGER.info(f'SMS for {number}: {sms}')

    def test_get_summary(self):
        summary = get_summary()
        LOGGER.info(f'Summary: {summary}')

    def test_get_mobilelist(self):
        summary = get_mobile_list()
        LOGGER.info(f'Mobile list: {summary}')
