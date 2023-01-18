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
    def handle(self, *args, **options):
        Total_accounts = list(Reddit_accounts.objects.all())
        print(len(Total_accounts))
        r = random.choice(Total_accounts)
        print(r)
        Total_accounts.remove(r)
        print(len(Total_accounts))
