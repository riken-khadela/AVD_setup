"""
This file contains all available follow actions.
"""
import time

from twbot.bot import TwitterBot
from twbot.models import UserAvd
from twbot.utils import *
import random


class RandomSwipeAction:
    """
    RandomAction: On user timeline

    algo:
    - Start twitter app
    - Click on twitter logo to refresh tweets page.
    - Perform random swipe_up actions with wait.
    - Perform random swipe_down actions with wait.
    """
    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name

    def get_new_tweet(self):
        # click on tweet logo to get new tweets
        tweet_logo_id = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/logo")'
        )
        tweet_log_xpath = self.driver().find_element_by_xpath(
            '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android'
            '.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget'
            '.LinearLayout/android.view.ViewGroup/android.widget.LinearLayout/android.view.ViewGroup/android.widget'
            '.FrameLayout/android.widget.ImageView '
        )
        tweet_logo = tweet_logo_id or tweet_log_xpath
        if tweet_logo:
            tweet_logo[0].click()
            print("*** Page refresh successfully ***")

    def swipe_down(self):
        _ = random.randrange
        start_x = _(100, 200)
        start_y = _(180, 220)
        end_x = _(80, 250)
        end_y = _(450, 550)
        duration = _(650, 850)
        self.driver().swipe(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration=duration
        )

    def swipe_up(self):
        _ = random.randrange
        start_x = _(100, 200)
        start_y = _(450, 550)
        end_x = _(80, 250)
        end_y = _(80, 120)
        duration = _(650, 850)
        self.driver().swipe(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration=duration
        )

    def get_top_tweet_else(self):
        top_tweet_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.TextView[@content-desc="Top Tweets on"]'
        )
        top_tweet_id = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/toolbar_timeline_switch")'
        )
        return top_tweet_id, top_tweet_xpath

    def get_latest_tweet_eles(self):
        latest_tweet_text = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/action_sheet_item_title")'
        )
        latest_tweet_logo = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/action_sheet_item_logo")'
        )
        return latest_tweet_text, latest_tweet_logo

    def check_and_load_home(self):
        restart_app(self.driver, 'twitter')

        # get top tweet element and click
        top_tweet_id, top_tweet_xpath = self.get_top_tweet_else()
        top_tweet = top_tweet_id or top_tweet_xpath
        if top_tweet:
            top_tweet[0].click()

            # get switch to latest tweet button element and click
            latest_tweet_text, latest_tweet_logo = self.get_latest_tweet_eles()
            latest_tweet = latest_tweet_text or latest_tweet_logo
            if latest_tweet:
                latest_tweet[0].click()

    @retry()
    def perform_action(self):
        restart_app(self.driver, 'twitter')
        self.check_and_load_home()
        self.get_new_tweet()

    @retry()
    def perform_random_swipe_action(self):
        restart_app(self.driver, 'twitter')
        self.check_and_load_home()
        self.get_new_tweet()

        # swipe up for number of random times
        for x in range(random.randrange(5, 15)):
            self.swipe_up()

        # swipe down for number of random times
        for y in range(random.randrange(5, 15)):
            self.swipe_down()

        self.get_new_tweet()
