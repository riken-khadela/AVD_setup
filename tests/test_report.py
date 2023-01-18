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
from twbot.report import ActionReport, get_this_week_total_actions
from twbot.report import *

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestReport(unittest.TestCase):

    def setUp(self):
        self.report = ActionReport()

    def test_get_stats(self):
        r = self.report.generate_action_stats_from_db()
        LOGGER.info(r)

    def test_generate_report(self):
        self.report.generate_action_report_excel()

    def test_generate_report_text(self):
        report_date = '2022-01-13'
        r = self.report.generate_action_report_text(report_date)
        LOGGER.info(f'\n{r}')

    def test_generate_report_text1(self):
        report_date = '2022-01-17'
        r = self.report.generate_action_report_text(report_date)
        LOGGER.info(f'\n{r}')

    def test_get_this_week_total_actions(self):
        actions = get_this_week_total_actions()

    def test_get_this_week_like_action(self):
        actions = get_this_week_like_action()

    def test_get_this_week_total_actions_for_one_account(self):
        target_user = 'xanalia_nft'
        target_user = 'nftnewznet'
        tweet_content = """The move from the digital ecosystem to MetaverseMetaverse will push the data usage 20 times across the globe.&hellip;"""
        actions = get_this_week_total_actions(target_user=target_user,
                tweet_content=tweet_content)
        LOGGER.info(actions)

    def test_get_this_week_like_action_for_one_account(self):
        target_user = 'nftnewznet'
        tweet_content = """The move from the digital ecosystem to MetaverseMetaverse will push the data usage 20 times across the globe.&hellip;"""
        actions = get_this_week_like_action(target_user=target_user,
                tweet_content=tweet_content)

    def test_get_this_week_retweet_action_for_one_account(self):
        target_user = 'nftnewznet'
        tweet_content = """The move from the digital ecosystem to MetaverseMetaverse will push the data usage 20 times across the globe.&hellip;"""
        actions = get_this_week_retweet_action(target_user=target_user,
                tweet_content=tweet_content)

    def test_get_this_week_statistics_of_actions(self):
        stats = get_this_week_statistics_of_actions()
        LOGGER.info(f'Statistics: {stats}')

    def test_print_this_week_stats(self):
        print_this_week_stats()

    def test_get_this_week_like_action_number(self):
        get_this_week_like_action_number()

    def test_get_this_week_retweet_action_number(self):
        get_this_week_retweet_action_number()

    def test_get_this_week_comment_action_number(self):
        get_this_week_comment_action_number()

    def test_get_this_week_like_action_number_for_one_account(self):
        target_user = 'nftnewznet'
        tweet_content = """The move from the digital ecosystem to MetaverseMetaverse will push the data usage 20 times across the globe.&hellip;"""
        get_this_week_like_action_number(target_user, tweet_content)

    def test_get_target_names_standard_and_nonstandard_for_one_day(self):
        get_target_names_standard_and_nonstandard_for_one_day()
