import os.path
import random
import subprocess

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
# Create your models here.
from django.db import models
from django.db.models import JSONField as JSONFieldPostgres
from django.db.models.signals import post_save, pre_delete

from conf import AVD_PACKAGES, AVD_DEVICES
from constants import ACC_BATCH
from core.models import User
# from django.contrib.auth.models import  User
from main import LOGGER
from twbot.cyberghostvpn import CyberGhostVpn
from twbot.vpn.nord_vpn import NordVpn


# Create your models here.
class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Reddit_accounts(models.Model):
    username = models.CharField(max_length=50,unique=True)
    profile_name = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    email = models.EmailField()
    avdname = models.CharField(max_length=50)
    def __str__(self):
        return self.username
    
class TwitterAccount(TimeStampModel):
    ACC_TYPE = (
        ("ART", "ART"),
        ("XANALIA_NFT", "XANALIA_NFT"),
        ("MKT_MEDIA", "MKT_MEDIA"),
    )

    STATUS = (
        ("ACTIVE", "ACTIVE"),
        ("TESTING", "TESTING"),
        ("INACTIVE", "INACTIVE"),
        ("BANNED", "BANNED"),
        ("SUSPENDED", "SUSPENDED"),
        ("LIMITED", "LIMITED"),
    )
    COUNTRIES = tuple((i,) * 2 for i in NordVpn.get_server_list())

    full_name = models.CharField(max_length=48, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS, default="ACTIVE")
    email = models.EmailField(max_length=255, null=True, blank=True)
    screen_name = models.CharField(max_length=15, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    password = models.CharField(max_length=40, null=True, blank=True)
    country = models.CharField(max_length=40, null=True, blank=True, choices=COUNTRIES)
    location = models.CharField(max_length=40, null=True, blank=True)
    profile_image = models.CharField(max_length=2048, null=True, blank=True)
    banner_image = models.CharField(max_length=2048, null=True, blank=True)
    account_type = models.CharField(
        max_length=100, choices=ACC_TYPE, null=True, blank=True
    )
    account_batch = models.CharField(
        max_length=100, choices=ACC_BATCH, null=True, blank=True
    )
    internal_following = models.ManyToManyField("self", blank=True)
    profile_updated = models.BooleanField(default=False)

    def __str__(self):
        return self.screen_name

class UserAvd(TimeStampModel):
    prox_type = (
        ("NORD_VPN", "NordVPN"),
        ("SURFSHARK", "SURFSHARK"),
        ("SMART_PROXY", "SMART_PROXY"),
        ("CYBERGHOST", "CYBERGHOST"),
    )

    COUNTRIES = tuple((i,) * 2 for i in CyberGhostVpn.get_server_list())
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avd_user")
    twitter_account = models.ForeignKey(TwitterAccount,
                                        null=True,
                                        blank=True,
                                        on_delete=models.CASCADE,
                                        related_name="avd_twitter_account")
    name = models.CharField(max_length=100, unique=True)
    port = models.IntegerField(unique=True)
    proxy_type = models.CharField(max_length=50, choices=prox_type, blank=True, null=True)
    country = models.CharField(max_length=40, choices=COUNTRIES, null=True, blank=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.name}:{self.port}"


def create_avd(sender, instance, **kwargs):
    from twbot.bot import TwitterBot
    created = kwargs.get('created')

    if created:
        LOGGER.info('Start to create AVD')
        try:
            # Initialize bot
            twbot = TwitterBot(instance.name, start_appium=False, start_adb=False)

            # Create avd
            twbot.create_avd(avd_name=instance.name)
            updated_config = os.path.join(settings.BASE_DIR, 'twbot/avd_config/config.ini')
            new_config_file = f"{settings.AVD_DIR_PATH}/{instance.name}.avd/config.ini"
            LOGGER.debug(f'updated_config: {updated_config}')
            LOGGER.debug(f'new_config_file: {new_config_file}')
            if os.path.isdir(settings.AVD_DIR_PATH) and \
                    os.path.isfile(new_config_file):
                # os.replace(updated_config, new_config_file)
                from shutil import copyfile
                copyfile(updated_config, new_config_file)

            print(f"**** AVD created with name: {instance.name} and port: {instance.port} ****")

        except Exception as e:
            # commands = [f'lsof -t -i tcp:{instance.port} | xargs kill -9',
            #                 f'lsof -t -i tcp:4724 | xargs kill -9']
            # for cmd in commands:
            #     p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
            instance.delete()
            print(f"Couldn't create avd due to the following error \n")
            print(e)


def create_better_avd(sender, instance, **kwargs):
    from twbot.bot import TwitterBot
    created = kwargs.get('created')

    if created:
        LOGGER.info('Start to create AVD')
        try:
            # Initialize bot
            twbot = TwitterBot(instance.name, start_appium=False, start_adb=False)

            device = random.choice(AVD_DEVICES)  # get a random device
            package = random.choice(AVD_PACKAGES)  # get a random package
            twbot.create_avd(avd_name=instance.name, package=package,
                             device=device)

            LOGGER.info(f"**** AVD created with name: {instance.name} and port: {instance.port} ****")

        except Exception as e:
            # commands = [f'lsof -t -i tcp:{instance.port} | xargs kill -9',
            #                 f'lsof -t -i tcp:4724 | xargs kill -9']
            # for cmd in commands:
            #     p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
            instance.delete()
            LOGGER.error(f"Couldn't create avd due to the following error \n")
            LOGGER.error(e)


def delete_avd(sender, instance, **kwargs):
    try:
        cmd = f'avdmanager delete avd --name {instance.name}'
        p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        pass


#  post_save.connect(create_avd, sender=UserAvd)
post_save.connect(create_better_avd, sender=UserAvd)
pre_delete.connect(delete_avd, sender=UserAvd)


class TwitterActionLog(TimeStampModel):
    ACTION_TYPE = (
        ("LIKE", "LIKE"),
        ("TWEET", "TWEET"),
        ('LOGOUT', 'LOGOUT'),
        ("LIKE_ACTION", "LIKE_ACTION"),
        ("RETWEET_ACTION", "RETWEET_ACTION"),
        ("FOLLOW_ACTION", "FOLLOW_ACTION"),
        ('STARTING_DEVICE', 'STARTING_DEVICE'),
        ('CHECK_INSTALLATIONS', 'CHECK_INSTALLATIONS'),
        ('SHADOWSOCKS_CONNECTION', 'SHADOWSOCKS_CONNECTION'),
        ("LOGIN", "LOGIN"),
        ("FOLLOW", "FOLLOW"),
        ("UNFOLLOW", "UNFOLLOW"),
        ("TWEET_TEXT", "TWEET_TEXT"),
        ("TWEET_IMAGE", "TWEET_IMAGE"),
        ("RETWEET", "RETWEET"),
        ("RANDOM_ACTION", "RANDOM_ACTION"),
        ("ENGAGEMENT", "ENGAGEMENT")
    )
    STATUS = (
        ("SUCCESS", "SUCCESS"),
        ("FAIL", "FAIL")
    )

    avd = models.ForeignKey(
        UserAvd, blank=True, null=True, on_delete=models.CASCADE
    )
    action_type = models.CharField(
        max_length=32, choices=ACTION_TYPE, blank=True, null=True
    )
    status = models.CharField(
        max_length=32, choices=STATUS, blank=True, null=True
    )
    msg = JSONFieldPostgres(default=dict, blank=True, null=True)
    action = models.CharField(max_length=250, null=True, blank=True)
    error = JSONFieldPostgres(default=dict, blank=True, null=True)
    
class LetestMsg(TimeStampModel):
    CHANNEL = (
        ('ENGLISH','ENGLISH'),
        ('JP','JP')
    )
    message = models.TextField(null=False,blank=False)
    reaction = ArrayField(ArrayField(models.CharField(null=True,blank=True,max_length=50)))
    channel = models.CharField(max_length=100, choices=CHANNEL, default="ENGLISH")
    
    def __str__(self):
        return str(self.message)
class reaction_onAnnouncement(TimeStampModel):
    reaction_BY = models.ForeignKey(UserAvd,on_delete=models.CASCADE)
    reaction_ON = models.ForeignKey(LetestMsg,on_delete=models.CASCADE)
    reaction = models.CharField(max_length=50)
    