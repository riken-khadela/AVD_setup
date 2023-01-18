import time
import subprocess

from django.db import models
from constants import COUNTRIES
from urllib3.packages.six import u
from django.db.models import JSONField
from django.db.models.enums import Choices
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser
from django.db.models.signals import post_save, pre_delete


class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    """Helps Django work with our custom user model."""

    def create_user(self, email, username=None, password=None):
        """Creates a new user profile object."""

        if not email:
            raise ValueError("Users must have an email address.")
        if not username:
            username = email
        if not password:
            raise ValueError("Users must have an password.")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, password):
        """Creates and saves a new superuser with given details."""

        user = self.create_user(email, username, password)

        user.is_superuser = True
        user.is_staff = True

        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin, TimeStampModel):
    """To Store user basic information"""

    LANGUAGE_CHOICES = (
        ("en-us", "English"),
        ("ja", "Japanese"),
        ("ko", "Korean"),
        ("zh_CN", "Chinese"),
    )

    USER_TYPES = (
        ("marketing_team", "marketing_team"),
        ("tester", "tester"),
        ("user", "user"),
    )

    APP_CHOICES = (
        ("IG", "IG"),  # Instagram
        ("TT", "TT"),  # TikTok
        ("YT", "YT"),  # YouTube
        ("TW", "TW"),  # Twitter
        ("TL", "TL"),  # Telegram
    )

    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email_verified = models.BooleanField(default=False)
    app_choice = models.CharField(max_length=200, choices=APP_CHOICES, default="IG")
    user_type = models.CharField(max_length=200, choices=USER_TYPES, default="user")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    timezone = models.CharField(max_length=100, blank=True, null=True, default=None)
    user_language = models.CharField(
        default="en-us", choices=LANGUAGE_CHOICES, max_length=15
    )
    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = [
        "email",
    ]

    def __str__(self):
        return self.username


class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_otp = models.CharField(max_length=6, default="000000")

    def __str__(self):
        return str(self.user.username) + "_" + str(self.generated_otp)


class EngageTask(TimeStampModel):
    STASUES = (
        ("PENDING", "PENDING"),
        ("FAILED", "FAILED"),
        ("DONE", "DONE"),
        ("RUNNING", "RUNNING")
    )

    PCS = (
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6"),
        ("7", "7"),
        ("8", "8"),
        ("9", "9"),
        ("10", "10"),
        ("11", "11"),
        ("12", "12"),
        ("13", "13"),
        ("14", "14"),
        ("15", "15"),
        ("16", "16"),
        ("17", "17"),
        ("18", "18"),
        ("19", "19"),
        ("20", "20"),
        ("21", "21"),
        ("22", "22"),
        ("23", "23"),
        ("24", "24"),
        ("25", "25")
    )

    target_name = models.CharField(max_length=300)
    tweet_id = models.CharField(max_length=300, blank=True, null=True)
    status = models.CharField(max_length=200, choices=STASUES, default="PENDING")
    system_no = models.CharField(max_length=3, choices=PCS, blank=True, null=True)

    def __str__(self):
        return f"{self.tweet_id} | {self.target_name} | {self.created} | {self.status}"
