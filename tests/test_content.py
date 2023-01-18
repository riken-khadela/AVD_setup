import unittest
import os
import django
import appium
import subprocess
import random
import requests

from appium.webdriver.appium_service import AppiumService
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from PIL import Image

from log import Log
from utils import set_log, reduce_img_size
from conf import PRJ_PATH
from conf import LOG_LEVEL, LOG_DIR, LOG_IN_ONE_FILE
from conf import TWEET_ENDPOINT, COMMENT_ENDPOINT
from accounts_conf import TWEET_KEYWORDS
from tweets import TWEETS, ENGLISH_TWEETS

# setup django settings
from django.conf import settings
if not os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surviral_avd.settings')
django.setup()

from twbot.bot import TwitterBot
from twbot.utils import start_app, random_sleep, get_comment_from_db
from utils import get_comment

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestContent(unittest.TestCase):

    timeout = 300

    def test_tweet(self):
        keyword = 'nft'
        data = {'keyword': keyword}

        keyword = 'nft'
        data = {'text': keyword}

        LOGGER.info(f'Start request with the keyword: {keyword}')
        r = requests.post(TWEET_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'tweet: {r.text}')

    def test_tweet_json(self):
        #  keyword = 'nft'
        #  data = {'keyword': keyword}
        keyword = 'nft'
        data = {'text': keyword}

        LOGGER.info(f'Start request with the keyword: {keyword}')
        r = requests.post(TWEET_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'tweet: {r.json()}')

    def test_tweet_2_keywords(self):
        #  keyword = 'nft, C++'
        #  data = {'keyword': keyword}
        keyword = 'nft, C++'
        data = {'text': keyword}

        LOGGER.info(f'Start request with the keyword: {keyword}')
        r = requests.post(TWEET_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'tweet: {r.text}')

    def test_tweet_blank(self):
        #  keyword = ''
        #  data = {'keyword': keyword}
        keyword = ''
        data = {'text': keyword}

        LOGGER.info(f'Start request with the keyword: {keyword}')
        r = requests.post(TWEET_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'tweet: {r.text}')

    def test_tweet_random_keyword(self):
        #  keyword = random.choice(TWEET_KEYWORDS)
        #  data = {'keyword': keyword}
        keyword = random.choice(TWEET_KEYWORDS)
        data = {'text': keyword}

        LOGGER.info(f'Start request with the keyword: {keyword}')
        r = requests.post(TWEET_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'tweet: {r.text}')

    def test_comment(self):
        text = 'I Love Football'
        data = {'text': text}

        LOGGER.info(f'Start request with the text: {text}')
        r = requests.post(COMMENT_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'comment: {r.json()}')

    def test_comment_blank(self):
        text = ''
        data = {'text': text}

        LOGGER.info(f'Start request with the text: {text}')
        r = requests.post(COMMENT_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'comment: {r.json()}')

    def test_comment_random(self):
        text = random.choice(TWEETS)
        data = {'text': text}

        LOGGER.info(f'Start request with the text: {text}')
        r = requests.post(COMMENT_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'comment: {r.json()}')

    def test_english_comment_random(self):
        text = random.choice(ENGLISH_TWEETS)
        data = {'text': text}

        LOGGER.info(f'Start request with the text: {text}')
        r = requests.post(COMMENT_ENDPOINT, data=data, timeout=self.timeout)
        LOGGER.info(f'status code: {r.status_code}')
        LOGGER.info(f'comment: {r.json()}')

    def test_english_comment_api_random(self):
        text = random.choice(ENGLISH_TWEETS)
        comment = get_comment(text)
        LOGGER.info(f'comment: {comment}')

    def test_english_comment_random_from_db(self):
        text = random.choice(ENGLISH_TWEETS)
        data = {'text': text}

        #  LOGGER.info(f'Start request with the text: {text}')
        retry_times = 3
        timeout = 1200
        is_used = True
        c = get_comment_from_db(text, retry_times, timeout, is_used=is_used)
        LOGGER.info(f'comment: {c}')

    def test_english_comment_for_exist_tweet_from_db(self):
        text = '''My inclusion on this list is a testament to the determination of the Taiwanese people to protect our democracy. I hope that #Taiwan's resilience in the face of challenges can inspire women around the world to make a difference in their communities & on the international stage.'''
        data = {'text': text}

        #  LOGGER.info(f'Start request with the text: {text}')
        retry_times = 3
        timeout = 1200
        is_used = True
        c = get_comment_from_db(text, retry_times, timeout, is_used=is_used)
        LOGGER.info(f'comment: {c}')
