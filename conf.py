# Configuration file
import logging
from pathlib import Path

# Project
PRJ_PATH = Path(__file__).parent

# Log
LOG_DIR = 'logs'
LOG_DIR_PATH = PRJ_PATH / 'logs'
LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)  # create it if it doesn't exist
LOG_LEVEL = logging.DEBUG
LOG_IN_ONE_FILE = True

# AVD
AVD_DEVICES = ["Nexus 10", "Nexus 4", "Nexus 5", "Nexus 5X", "Nexus 6",
               "Nexus 6P", "Nexus 7 2013", "Nexus 7", "Nexus 9",
               "pixel", "pixel_2", "pixel_2_xl", "pixel_3", "pixel_3_xl",
               "pixel_3a", "pixel_3a_xl", "pixel_4", "pixel_4_xl", "pixel_4a",
               "pixel_5", "pixel_xl", "pixel_c",
               ]
AVD_PACKAGES = ["system-images;android-28;default;x86",
                "system-images;android-28;default;x86_64",
                "system-images;android-29;default;x86",
                "system-images;android-29;default;x86_64",
                "system-images;android-30;default;x86_64",

                # cause some errors of twitter: (errors: timestamp out of bounds, code:135)
                #  "system-images;android-31;default;x86_64",
                ]

US_TIMEZONE = ['US/Alaska', 'US/Aleutian', 'US/Arizona', 'US/Central',
               'US/East-Indiana', 'US/Eastern', 'US/Hawaii', 'US/Indiana-Starke',
               'US/Michigan', 'US/Mountain', 'US/Pacific', 'US/Samoa']

# time
WAIT_TIME = 30

# twitter
# twitter version for apk, find it in the directory 'apk/twitter_<version>.apk'
# please download more apks, and put them into 'apk/', and update the variable
# This version ‘9.11.0-release.00’ and the following versions require google play services.
TWITTER_VERSIONS = [
    '8.84.0-release.00',
    # '9.0.0-release.00',
    # '9.2.0-release.00',
    # '9.3.0-release.00',
    '9.4.0-release.00',
    '9.6.0-release.01',
    '9.7.0-release.00',
    '9.9.0-release.00',

    #  '9.11.0-release.00',
    #  '9.13.0-release.00',
    #  '9.16.1-release.00',
    #  '9.18.0-release.00',
    #  '9.19.0-release.00',
]

# deathbycaptcha.com account
DBC_USERNAME = 'noborderz'
DBC_PASSWORD = '/+eQm@>;Q:Td8?MA'

# captcha
RECAPTCHA_ALL_RETRY_TIMES = 15  # the number of captcha images to resolve in all
FUNCAPTCHA_ALL_RETRY_TIMES = 20  # the number of captcha images to resolve in all
CAPTCHA_IMAGE_DIR_NAME = 'temp'
CAPTCHA_IMAGE_DIR = PRJ_PATH / CAPTCHA_IMAGE_DIR_NAME
CAPTCHA_IMAGE_DIR.mkdir(parents=True, exist_ok=True)  # create it if it doesn't exist

# account
PROFILE_IMAGE_DIR_NAME = 'images'
PROFILE_IMAGE_DIR = PRJ_PATH / PROFILE_IMAGE_DIR_NAME
PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)  # create it if it doesn't exist

# content
#  TWEET_ENDPOINT = 'http://203.101.178.213:8000/article_generation/'
TWEET_ENDPOINT = 'http://203.101.178.213:8003/tweet_gen/'
COMMENT_ENDPOINT = 'http://203.101.178.213:8003/parlai_chatbot/'
ACCOUNTS_MAX_NUMBER_FOR_TWEET = 10  # for command: write_tweet
ACCESS_TIMEOUT_FOR_API_SERVER = 10

# outputs
OUTPUTS_DIR_NAME = 'outputs'
OUTPUTS_DIR = PRJ_PATH / OUTPUTS_DIR_NAME
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)  # create it if it doesn't exist

# tasks
TASKS_DIR_NAME = 'tasks'
TASKS_DIR = PRJ_PATH / TASKS_DIR_NAME
TASKS_DIR.mkdir(parents=True, exist_ok=True)  # create it if it doesn't exist

# Initial data
#  FIXTURES_DIR_NAME = 'fixtures'
#  FIXTURES_DIR = PRJ_PATH / FIXTURES_DIR_NAME
#  FIXTURES_DIR.mkdir(parents=True, exist_ok=True) # create it if it doesn't exist

# installation packages
PACKAGES_DIR_NAME = 'apk'
PACKAGES_DIR = PRJ_PATH / PACKAGES_DIR_NAME
PACKAGES_DIR.mkdir(parents=True, exist_ok=True)  # create it if it doesn't exist
# cyberghostvpn
CYBERGHOSTVPN_APK = PACKAGES_DIR / 'cyberghostvpn_8.6.4.396.apk'
CYBERGHOSTVPN_SERVERS = {
    'Albania': [],
    'Algeria': [],
    'Andorra': [],
    'Argentina': [],
    'Armenia': [],
    'Australia': ['Melbourne', 'Sydney'],
    'Austria': [],
    'Bahamas': [],
    'Bangladesh': [],
    'Belarus': [],
    'Belgium': [],
    'Bosnia & Herzegovina': [],
    'Brazil': [],
    'Bulgaria': [],
    'Cambodia': [],
    'Canada': ['Montreal', 'Toronto', 'Vancouver'],
    'Chile': [],
    'China': [],
    'Colombia': [],
    'Costa Rica': [],
    'Croatia': [],
    'Cyprus': [],
    'Czechia': [],
    'Denmark': [],
    'Egypt': [],
    'Estonia': [],
    'Finland': [],
    'France': ['Paris', 'Strasbourg'],
    'Georgia': [],
    'Germany': ['Berlin', 'Dusseldorf', 'Frankfurt'],
    'Greece': [],
    'Greenland': [],
    'Hong Kong': [],
    'Hungary': [],
    'Iceland': [],
    'India': [],
    'Indonesia': [],
    'Iran': [],
    'Ireland': [],
    'Isle of Man': [],
    'Israel': [],
    'Italy': ['Milano', 'Rome'],
    'Japan': [],
    'Kazakhstan': [],
    'Kenya': [],
    'Latvia': [],
    'Liechtenstein': [],
    'Lithuania': [],
    'Luxembourg': [],
    'Macau': [],
    'Macedonia (FYROM)': [],
    'Malaysia': [],
    'Malta': [],
    'Mexico': [],
    'Moldova': [],
    'Monaco': [],
    'Mongolia': [],
    'Montenegro': [],
    'Morocco': [],
    'Netherlands': [],
    'New Zealand': [],
    'Nigeria': [],
    'Norway': [],
    'Pakistan': [],
    'Panama': [],
    'Philippines': [],
    'Poland': [],
    'Portugal': [],
    'Qatar': [],
    'Romania': ['Bucharest', 'NoSpy Bucharest'],
    'Russia': [],
    'Saudi Arabia': [],
    'Serbia': [],
    'Singapore': [],
    'Slovakia': [],
    'Slovenia': [],
    'South Africa': [],
    'South Korea': [],
    'Spain': ['Barcelona', 'Madrid'],
    'Sri Lanka': [],
    'Sweden': [],
    'Switzerland': ['Huenenberg', 'Zurich'],
    'Taiwan': [],
    'Thailand': [],
    'Turkey': [],
    'Ukraine': [],
    'United States': [],
    'United Kingdom': ['Berkshire', 'London', 'Manchester'],
    'United States': [
        'Atlanta',
        'Chicago',
        'Dallas',
        'Las Vegas',
        'Los Angeles',
        'Miami',
        'New York',
        'Los Angeles',
        'Miami',
        'New York',
        'Phoenix',
        'San Francisco',
        'Seattle',
        'Washington'
    ],
    'Venezuela': [],
    'Vietnam': []
}

# appium
APPIUM_SERVER_HOST = '127.0.0.1'
APPIUM_SERVER_PORT = 4724
APPIUM_SERVER_PORTS = list(range(APPIUM_SERVER_PORT, APPIUM_SERVER_PORT + 100))
#  SYSTEM_PORTS = list(range(8200, 8300))
SYSTEM_PORTS = list(range(8200, 8328))
# adb
ADB_SERVER_HOST = '127.0.0.1'
ADB_SERVER_PORT = 5037
ADB_CONSOLE_PORTS = list(range(5554, 5682, 2))

# parallel
PARALLEL_NUMER = 1

# Slack Web Hook
WEB_HOOK_URL = "https://hooks.slack.com/services/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"

# MAX ACTIVE ACCOUNTS
MAX_ACTIVE_ACCOUNTS = 250

# Required percentage of active accounts
MIN_ACTIVE_ACCOUNTS_PERCENTAGE = 0.7  # 70%
MAX_ACCOUNTS_CREATION_PER_DAY = 20
