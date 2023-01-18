import sys
import time
from concurrent import futures

import numpy as np
from django.core.management.base import BaseCommand

from conf import US_TIMEZONE, PARALLEL_NUMER
from core.models import User
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.actions.follow import *
from twbot.bot import *


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument('-n')
        parser.add_argument('-m', '--run_times', type=int, default=0,
                            help='After the run times, the bot will exit(0 means no effect)')
        parser.add_argument(
            "--no_vpn",
            type=bool,
            nargs="?",
            const=True,
            default=False,
            help="Whether to use VPN or not, if it presents, don't use VPN.",
        )
        parser.add_argument(
            '--parallel_number',
            nargs='?',
            default=PARALLEL_NUMER,
            type=int,
            help=(f'Number of parallel running. Default: {PARALLEL_NUMER}'
                  '(PARALLEL_NUMER in the file conf.py)')
        )

    def run_tasks(self):
        count = 0
        process_complete = 0

        Total_accounts = list(Reddit_accounts.objects.all())
        # if len(Total_accounts) < required_accounts:
        #     print('\n\n','*'*5,'You can not user more accounts than you have in DATABASE','*'*5,'\n\n')
        #     return 
        required_accounts = len(Total_accounts)
        while process_complete < required_accounts:
            reddit_user = random.choice(Total_accounts)
            for i in range(2):
                # fix the error
                # psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "twbot_useravd_port_key"
                # DETAIL:  Key (port)=(5794) already exists.
                user_avd = reddit_user.avdname
                country, city = CyberGhostVpn.get_random_usa_server()
                LOGGER.debug(f'country: {country}, City: {city}')
                try:
                
                    LOGGER.debug(f'AVD USER: {user_avd}')

                    # tb = TwitterBot('android_368')
                    tb = TwitterBot('user_avd.name')

                    # Connect vpn
                    if not self.no_vpn:
                        time.sleep(10)
                        if not tb.connect_to_vpn(country=country, city=city):
                            raise Exception("Couldn't able to connect Cyberghost VPN")
                    else:
                        tb.check_apk_installation()
                    accounts_created_bool = tb.create_account()
                    # time.sleep(300)

                    if accounts_created_bool == True:
                        process_complete += 1

                except GetSmsCodeNotEnoughBalance as e:
                    LOGGER.debug('Not enough balance in GetSMSCode')
                    tb.kill_bot_process(True, True)
                    sys.exit(1)
                except Exception as e:
                    print(traceback.format_exc())
                    try:
                        tb.kill_bot_process(True, True)
                        # user_avd.delete() if user_avd else None
                    except:
                        pass
                finally:
                    if self.run_times != 0:
                        count += 1
                        if count >= self.run_times:
                            LOGGER.info(f'Real run times: {count}, now exit')
                            break

                    if 'tb' in locals() or 'tb' in globals():
                        LOGGER.info(f'Clean the bot: {user_avd}')
                        self.clean_bot(tb, False)
                    else:
                        name = user_avd.name
                        port = ''
                        parallel.stop_avd(name=name, port=port)
            Total_accounts.remove(reddit_user)
            process_complete += 1

    def handle(self, *args, **options):
        self.total_accounts_created = 0
        self.avd_pack = []
        if UserAvd.objects.all().count() >= 500:
            return "Cannot create more than 500 AVDs please delete existing to create a new one."

        required_accounts = int(options.get('n'))

        self.no_vpn = options.get('no_vpn')
        self.parallel_number = options.get('parallel_number')

        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')
        requied_account_list = [n.size for n in
                                np.array_split(np.array(range(required_accounts)), self.parallel_number)]
        with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
            for i in range(self.parallel_number):
                executor.submit(self.run_tasks)
        print(f" All created UserAvd and TwitterAccount ****\n")
        print(self.avd_pack)
        for x, y in self.avd_pack:
            uavd = UserAvd.objects.filter(id=x)
            tw_ac = TwitterAccount.objects.filter(id=y)
            if uavd and tw_ac:
                UserAvd.objects.filter(id=x).update(twitter_account_id=y)

        random_sleep(10, 30)

    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(60, 80)
