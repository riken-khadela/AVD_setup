import os
import django
import argparse

from log import Log
from utils import set_log
from conf import PRJ_PATH
from conf import LOG_LEVEL, LOG_DIR, LOG_IN_ONE_FILE

# setup django settings
from django.conf import settings
if not os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surviral_avd.settings')
django.setup()

from twbot.models import UserAvd, TwitterAccount
from twbot.utils import get_twitter_number, get_twitter_sms, get_summary
from twbot.bot import TwitterBot as TB

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)

def move_account_between_avds(src, dest):
    src_avd = UserAvd.objects.get(name=src)
    dest_avd = UserAvd.objects.get(name=dest)
    LOGGER.debug(f'src avd: {src_avd}')
    LOGGER.debug(f'dest avd: {dest_avd}')

    if src_avd.twitter_account:
        dest_avd.twitter_account = src_avd.twitter_account
        #  dest_avd.timezone = src_avd.timezone
        #  dest_avd.country = src_avd.country
        dest_avd.save()

    src_avd.twitter_account = None
    src_avd.save()

    LOGGER.debug(f'Moved the twitter account of src avd to dest avd')

def check_account_for_avd(avd_name, login=False):
    avd = UserAvd.objects.get(name=avd_name)
    account = avd.twitter_account

    tb = TB(avd.name)
    driver = tb.driver()
    LOGGER.info(f"*** Start up {tb.emulator_name} ***")
    LOGGER.info(f'Username: {account.screen_name}'
            f' password: {account.password}'
            f' phone: {account.phone}')
    
    # Confirm Login Status
    if login:
        tb.perform_login()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Main UI for some tools')
    parser.add_argument('-s', '--sms', dest='sms', type=str,
            help='Get SMS for a mobile number')
    parser.add_argument('-a', '--move_account', dest='avd_account', nargs=2,
            type=str, help='Move account from source avd to destination avd')
    parser.add_argument('--avd', dest='avd', type=str,
            help='Start up an AVD to check account')

    args = parser.parse_args()

    if args.sms:
        print(get_twitter_sms(args.sms))

    if args.avd_account:
        move_account_between_avds(args.avd_account[0], args.avd_account[1])

    if args.avd:
        check_account_for_avd(args.avd)

