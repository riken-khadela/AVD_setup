import unittest
import os
import django
import appium
import subprocess
import random

from appium.webdriver.appium_service import AppiumService
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from PIL import Image

from log import Log
from utils import set_log, reduce_img_size
from conf import PRJ_PATH
from conf import LOG_LEVEL, LOG_DIR, LOG_IN_ONE_FILE
from pathlib import Path

# setup django settings
from django.conf import settings
if not os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surviral_avd.settings')
django.setup()

from twbot.bot import TwitterBot
from twbot.utils import start_app, random_sleep
#  from verify import Funcaptcha
from verify import DeathByCaptchaUI
from utils import reduce_img_size, restrict_image_size
from parallel import *

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestParallel(unittest.TestCase):

    def test_start_avd(self):
        kwargs = {
            'avd': 'android_318',
            'timezone': 'US/Michigan',
            'port': 5558,
        }
        result = start_avd(**kwargs)
        LOGGER.info(f'result: {result}')
        LOGGER.info(f'pid: {result.pid}')
        LOGGER.info(f'returncode: {result.returncode}')
        #  result.kill()

    def test_get_all_avd_commands(self):
        verbose = False
        result = get_all_avd_commands(verbose=verbose)
        LOGGER.info(f'result: {result}')

    def test_get_running_system_ports(self):
        result = get_running_system_ports()
        LOGGER.info(f'result: {result}')

    def test_get_available_system_ports(self):
        result = get_available_system_ports()
        LOGGER.info(f'result: {result}')

    def test_get_avd_pid(self):
        name = 'android_318'
        port = '5558'
        result = get_avd_pid(name=name, port=port)
        LOGGER.info(f'result: {result}')

    def test_get_listening_adb_pid(self):
        result = get_listening_adb_pid()
        LOGGER.info(f'result: {result}')

    def test_get_avd_pid_all(self):
        name = 'android_480'
        port = '5880'
        result = get_avd_pid(name=name, port=port)
        LOGGER.info(f'result: {result}')

    def test_get_avd_pid_name(self):
        name = 'android_480'
        port = ''
        result = get_avd_pid(name=name, port=port)
        LOGGER.info(f'result: {result}')

    def test_get_avd_pid_port(self):
        name = ''
        port = '5880'
        result = get_avd_pid(name=name, port=port)
        LOGGER.info(f'result: {result}')

    def test_stop_avd(self):
        name = 'android_480'
        port = '5880'
        result = stop_avd(name=name, port=port)
        LOGGER.info(f'result: {result}')
