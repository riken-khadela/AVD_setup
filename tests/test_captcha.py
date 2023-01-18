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

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestImage(unittest.TestCase):

    img_file = Path(__file__).parent / 'FunCaptcha.png'
    restrict_size = 1024 * 180  # 180KB

    def test_reduce_image_factor_1(self):
        reduce_factor = 1
        small_img = reduce_img_size(self.img_file, reduce_factor)

    def test_reduce_image_factor_2(self):
        reduce_factor = 2
        small_img = reduce_img_size(self.img_file, reduce_factor)

    def test_restrict_image_size(self):
        reduce_step = 0.125
        reduce_factor = 1
        (small_img, last_reduce_factor) = restrict_image_size(self.img_file, reduce_factor,
                reduce_step, self.restrict_size)

class TestFuncaptchaApi(unittest.TestCase):
    img_file = Path(__file__).parent / 'FunCaptcha.png'

    def setUp(self):
        self.client = DeathByCaptchaUI()

    def test_get_balance(self):
        balance = self.client.get_balance()
        self.assertGreater(balance, 0)

    def test_resolve_captcha_ui_funcaptcha(self):
        reduce_factor = 1
        result = self.client.resolve_newrecaptcha_with_coordinates_api_ui(
                self.img_file, reduce_factor)
        LOGGER.debug(f'result: {result}')
        self.assertTrue(result)

    def test_resolve_captcha_ui_factor2(self):
        reduce_factor = 2
        result = self.client.resolve_newrecaptcha_with_coordinates_api_ui(
                self.img_file, reduce_factor)
        LOGGER.debug(f'result: {result}')
        self.assertTrue(result)

    def test_resolve_captcha_ui_bus(self):
        img_file = Path('./tests/recaptcha_bus.png')
        reduce_factor = 1
        result = self.client.resolve_newrecaptcha_with_coordinates_api_ui(
                img_file, reduce_factor)
        LOGGER.debug(f'result: {result}')
        self.assertTrue(result)

    def test_resolve_captcha_ui_vehicle(self):
        img_file = Path('./tests/recaptcha_vehicles.png')
        reduce_factor = 1
        reduce_step = 0.5
        result = self.client.resolve_newrecaptcha_with_coordinates_api_ui(
                img_file, reduce_factor, reduce_step)
        LOGGER.debug(f'result: {result}')
        self.assertTrue(result)

    def test_resolve_captcha_ui_light(self):
        img_file = Path('./tests/recaptcha_traffic_light.png')
        reduce_factor = 1
        reduce_step = 0.125
        result = self.client.resolve_newrecaptcha_with_coordinates_api_ui(
                img_file, reduce_factor, reduce_step)
        LOGGER.debug(f'result: {result}')
        self.assertTrue(result)
