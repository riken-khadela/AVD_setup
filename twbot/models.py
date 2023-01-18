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
from core.models import User, TimeStampModel
from main import LOGGER
from twbot.cyberghostvpn import CyberGhostVpn
from twbot.vpn.nord_vpn import NordVpn


# Create your models here.

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

    other_following = models.ManyToManyField("TwitterOtherAccount", blank=True)
    profile_updated = models.BooleanField(default=False)

    def __str__(self):
        return self.screen_name

class Phone(TimeStampModel):
    number = models.CharField(max_length=15, null=True, blank=True)
    pid = models.CharField(max_length=8, null=True, blank=True)
    user = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING,
            null=True, blank=True, related_name='number')
    is_banned = models.BooleanField(default=False)
    ban_result = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.number

class Sms(TimeStampModel):
    number = models.ForeignKey(Phone, on_delete=models.DO_NOTHING)
    content = models.CharField(max_length=256)

    CREATE_ACCOUNT = 1
    VERIFY_ACCOUNT = 2
    PURPOSE = (
        (CREATE_ACCOUNT, "For creating account"),
        (VERIFY_ACCOUNT, "For verifying account"),
    )
    purpose = models.SmallIntegerField(choices=PURPOSE, null=True, blank=True)

    def __str__(self):
        return f'{self.number}, {self.content}'

class TwitterTargetAccount(TimeStampModel):
    STATUS = (
        ("ACTIVE", "ACTIVE"),
        ("TESTING", "TESTING"),
        ("INACTIVE", "INACTIVE"),
        ("BANNED", "BANNED"),
        ("SUSPENDED", "SUSPENDED"),
    )

    full_name = models.CharField(max_length=48, null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS, default="ACTIVE")
    screen_name = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.screen_name or self.full_name


class TwitterOtherAccount(TimeStampModel):
    STATUS = (
        ("ACTIVE", "ACTIVE"),
        ("TESTING", "TESTING"),
        ("INACTIVE", "INACTIVE"),
        ("BANNED", "BANNED"),
        ("SUSPENDED", "SUSPENDED"),
    )

    full_name = models.CharField(max_length=48, null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS, default="ACTIVE")
    screen_name = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.screen_name or self.full_name


class TwitterUser(TimeStampModel):
    username = models.CharField(max_length=255, null=True, blank=True)
    screen_name = models.CharField(max_length=255, null=True, blank=True)


class ActionType(TimeStampModel):
    CREATE_ACCOUNT = 1
    FOLLOW_ACCOUNT = 2
    LIKE_TWEET = 3
    RETWEET_TWEET = 4
    COMMENT_TWEET = 5
    CREATE_TWEET = 6
    LOGIN_APP = 7
    LOGOUT_APP = 8
    UNFOLLOW_ACCOUNT = 9

    ACTION_TYPE = (
        (CREATE_ACCOUNT, "Create an account"),
        (FOLLOW_ACCOUNT, "Follow an account"),
        (LIKE_TWEET, "Like a tweet"),
        (RETWEET_TWEET, "Retweet a tweet"),
        (COMMENT_TWEET, "Comment on a tweet"),
        (CREATE_TWEET, "Create a tweet"),
        (LOGIN_APP, 'Login twitter'),
        (LOGOUT_APP, "Logout twitter"),
        (UNFOLLOW_ACCOUNT, "Unfollow an account"),
    )

    id = models.SmallIntegerField(choices=ACTION_TYPE, primary_key=True)
    text = models.CharField(max_length=64, blank=True, null=True)
    remark = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.text


class ActionResult:
    SUCCESSFUL = 0
    FAILED = 1
    RESULT = (
        (SUCCESSFUL, 'Successful'),
        (FAILED, 'Failed'),
    )


class ActionForBotAccount(TimeStampModel):
    owner = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING)
    action = models.ForeignKey(ActionType, on_delete=models.DO_NOTHING)
    result = models.SmallIntegerField(choices=ActionResult.RESULT)
    object = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING,
                               null=True, blank=True, related_name='object')

    def __str__(self):
        return f"Action owner: {self.owner}, action: {self.action}"


class ActionForTargetAccount(TimeStampModel):
    owner = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING)
    action = models.ForeignKey(ActionType, on_delete=models.DO_NOTHING)
    result = models.SmallIntegerField(choices=ActionResult.RESULT)
    object = models.ForeignKey(TwitterTargetAccount,
            on_delete=models.DO_NOTHING, null=True, blank=True)
    tweet = models.ForeignKey('TweetForTargetAccount',
            on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return f"Action owner: {self.owner}, action: {self.action}"


class ActionForOtherAccount(TimeStampModel):
    owner = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING)
    action = models.ForeignKey(ActionType, on_delete=models.DO_NOTHING)
    result = models.SmallIntegerField(choices=ActionResult.RESULT)
    object = models.ForeignKey(TwitterOtherAccount,
                               on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return f"Action owner: {self.owner}, action: {self.action}"


class CompetitorUserDetials(TimeStampModel):
    target_user = models.CharField(max_length=255, null=True, blank=True)
    followers = models.ManyToManyField(TwitterUser, related_name="followers")
    following = models.ManyToManyField(TwitterUser, related_name="following")


class TwitterJob(TimeStampModel):
    JOB_TYPE = (
        ("TWEET_TEXT", "TWEET_TEXT"),
        ("TWEET_IMAGE", "TWEET_IMAGE"),
        ("TWEET", "TWEET"),
        ("LIKE", "LIKE"),
        ("RETWEET", "RETWEET"),
        ("FOLLOW_SINGLE_USER", "FOLLOW_SINGLE_USER"),
        ("UNFOLLOW", "UNFOLLOW"),
        ("MULTIPLE_FOLLOW", "MULTIPLE_FOLLOW"),
    )
    JOB_STATUS = (
        ("P", "PENDING"),
        ("C", "COMPLETED"),
        ("F", "FAILED"),
        ("I", "In-progress"),
        ("CN", "CANCELED"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    twitter_account = models.ForeignKey(
        TwitterAccount, blank=True, null=True, on_delete=models.CASCADE
    )
    job_type = models.CharField(max_length=100, choices=JOB_TYPE)
    target_username = models.ManyToManyField(
        TwitterUser, related_name="target_insta_users"
    )
    status = models.CharField(max_length=2, choices=JOB_STATUS, blank=True, null=True)
    tweet_id = models.CharField(max_length=255, blank=True, null=True)
    image_path = models.CharField(max_length=255, blank=True, null=True)
    text_message = models.CharField(max_length=255, blank=True, null=True)
    follow_user = models.CharField(max_length=100, null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)


class Tweet(TimeStampModel):
    #  tweet_id = models.CharField(max_length=100, unique=True)
    tweet_id = models.CharField(max_length=100)
    text = models.CharField(max_length=1000, null=True, blank=True)
    image = ArrayField(
        models.CharField(max_length=500, default=" "), null=True, blank=True
    )
    tweeted = models.BooleanField(default=False)
    tweet_meta = JSONFieldPostgres(default=dict, blank=True, null=True)
    video = ArrayField(
        models.CharField(max_length=500, default=" "), null=True, blank=True
    )
    likes = models.CharField(max_length=50, null=True, blank=True)
    retweet = models.CharField(max_length=50, null=True, blank=True)
    screen_name = models.CharField(max_length=50, null=True, blank=True)
    status = models.BooleanField(default=False)

class TweetForTargetAccount(TimeStampModel):
    ACTIVE = 1
    DELETED = 2
    TWEET_STATUS = (
        (ACTIVE, "Active"),
        (DELETED, "Deleted"),
    )

    owner = models.ForeignKey(TwitterTargetAccount,
            on_delete=models.DO_NOTHING, null=True, blank=True)
    text = models.CharField(max_length=512, null=True, blank=True)
    publish_time = models.CharField(max_length=32, null=True, blank=True)
    like_count = models.CharField(max_length=16, null=True, blank=True)
    retrweet_count = models.CharField(max_length=16, null=True, blank=True)
    comment_count = models.CharField(max_length=16, null=True, blank=True)
    status = models.SmallIntegerField(choices=TWEET_STATUS, default=ACTIVE)
    is_retweeted = models.BooleanField(default=False)

    def __str__(self):
        #  return self.text
        return f'{self.id}'

class Comment(TimeStampModel):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000, null=True, blank=True)
    is_used = models.BooleanField(default=False)

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


class EngageTask(TimeStampModel):
    likes = models.IntegerField()
    follows = models.IntegerField()
    retweets = models.IntegerField()
    comments = models.IntegerField()
    failed = JSONFieldPostgres(default=dict, blank=True, null=True)
    comment_text = JSONFieldPostgres(default=dict, blank=True, null=True)
    batch = models.CharField(max_length=32, blank=True, null=True)
    tweet_url = models.CharField(max_length=2083, blank=True, null=True)


class UrlEngageTask(TimeStampModel):
    STATUS = (
        ("PENDING", "PENDING"),
        ("FAILED", "FAILED"),
        ("COMPLETED", "COMPLETED")
    )

    avds = models.ManyToManyField(UserAvd)
    tweet_url = models.CharField(max_length=2083, blank=True, null=True)
    status = models.CharField(max_length=32, choices=STATUS, blank=True, null=True, default="PENDING")
