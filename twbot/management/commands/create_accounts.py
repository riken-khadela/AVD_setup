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
        parser.add_argument('-n')
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

    def run_tasks(self, required_accounts):
        count = 0
        accounts_created = 0
        while accounts_created < required_accounts:
            # fix the error
            # psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "twbot_useravd_port_key"
            # DETAIL:  Key (port)=(5794) already exists.
            ports = list(
                filter(
                    lambda y: not UserAvd.objects.filter(port=y).exists(),
                    map(
                        lambda x: 5550 + x, range(1, 500)
                    )
                )
            )
            devices = list(
                filter(
                    lambda y: not UserAvd.objects.filter(name=y).exists(),
                    map(
                        lambda x: f"android_{x}", range(1, 500)
                    )
                )
            )
            start_time = time.time()
            avd_name = random.choice(devices)
            port = random.choice(ports)

            # create all accounts in USA
            country, city = CyberGhostVpn.get_random_usa_server()
            LOGGER.debug(f'country: {country}, City: {city}')
            try:
                # create an avd user, at the same time, creat the relative AVD
                # before deleting this avd user, first deleting the relative AVD
                LOGGER.debug('Start to creating AVD user')

                # if the country is USA, then create timezone for AVD
                if 'united states' in country.lower():
                    user_avd = UserAvd.objects.create(
                        user=User.objects.all().first(),
                        name=avd_name,
                        port=port,
                        proxy_type="CYBERGHOST",
                        country=country,
                        timezone=random.choice(US_TIMEZONE),
                    )
                else:
                    user_avd = UserAvd.objects.create(
                        user=User.objects.all().first(),
                        name=avd_name,
                        port=port,
                        proxy_type="CYBERGHOST",
                        country=country
                    )

                LOGGER.debug(f'AVD USER: {user_avd}')

                # tb = TwitterBot('android_368')
                tb = TwitterBot(user_avd.name)

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
                    accounts_created += 1

            except GetSmsCodeNotEnoughBalance as e:
                LOGGER.debug('Not enough balance in GetSMSCode')
                tb.kill_bot_process(True, True)
                sys.exit(1)
            except Exception as e:
                print(traceback.format_exc())
                try:
                    tb.kill_bot_process(True, True)
                    user_avd.delete() if user_avd else None
                except:
                    pass
            finally:
                if self.run_times != 0:
                    count += 1
                    if count >= self.run_times:
                        LOGGER.info(f'Real run times: {count}, now exit')
                        break

                if 'tb' in locals() or 'tb' in globals():
                    LOGGER.info(f'Clean the bot: {user_avd.name}')
                    self.clean_bot(tb, False)
                else:
                    name = user_avd.name
                    port = ''
                    parallel.stop_avd(name=name, port=port)

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
                executor.submit(self.run_tasks, requied_account_list[i])
        print(f" All created UserAvd and TwitterAccount ****\n")
        
        random_sleep(10, 30)

    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(60, 80)
