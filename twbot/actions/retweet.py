"""
This file contains all available comment actions.
"""
import time

from appium.webdriver.common.touch_action import TouchAction

from twbot.bot import TwitterBot
from twbot.models import UserAvd
from twbot.utils import *


class RetweetActionOne:
    """
        algo:
        - Start twitter app
        - Click on search button
        - Click on search bar and type target username
        - Click retweet icon of his first tweet
        - Click on text "Retweet"
        """

    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name

    def get_search_els_1(self):
        """
        get_search_els_1: Returns available search tab elements
        """

        ele_one = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view"
            ".ViewGroup/android.widget.FrameLayout["
            "2]/android.view.ViewGroup/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget"
            ".LinearLayout[2]/android.view.View "
        )
        ele_two = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view"
            ".ViewGroup/android.widget.FrameLayout["
            "2]/android.view.ViewGroup/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget"
            ".LinearLayout[2] "
        )
        return ele_one, ele_two

    def get_search_els_2(self):
        """
        get_search_els_2: Returns available search tab elements
        """

        ele_one = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget"
            ".LinearLayout/android.widget.FrameLayout/android.widget.HorizontalScrollView/android.widget.LinearLayout"
            "/android.widget.LinearLayout[2] "
        )
        ele_two = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget"
            ".LinearLayout/android.widget.FrameLayout/android.widget.HorizontalScrollView/android.widget.LinearLayout"
            "/android.widget.LinearLayout[2]/android.view.View "
        )
        return ele_one, ele_two

    def get_search_bar_els(self):
        """
        get_search_bar_els: Returns available elements of search bar
        """
        ele_one = self.driver().find_elements_by_xpath(
            '//android.widget.RelativeLayout[@content-desc="Search Twitter"]'
        )
        ele_two = self.driver().find_elements_by_xpath(
            '//android.widget.RelativeLayout[@content-desc="Search Twitter"]/android.widget.TextView'
        )
        return ele_one, ele_two

    def goto_search(self):
        """
        goto_search: Click on search button from home page and load
        """

        ele_one, ele_two = self.get_search_els_1()
        search = ele_one or ele_two
        if search:
            search[0].click()
            time.sleep(5)
            return True

        ele_one, ele_two = self.get_search_els_2()
        search = ele_one or ele_two
        if search:
            search[0].click()
            time.sleep(5)
            return True

    def input_text_in_search_bar(self):
        """
        input_text_in_search_bar: Types target username text in search bar
        """
        search_bar = self.driver().find_elements_by_xpath(
            '//android.widget.EditText[@content-desc="Search"]'
        )
        search_bar[0].send_keys(str(self.target_name))

    def click_on_first_tab(self):
        """
        click_on_people_tab: Clicks on people tab on search page.
        """

        target_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Top"]'
        )
        target_xpath2 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Top"]/android.widget.TextView'
        )
        target_xpath = target_xpath1 or target_xpath2
        target_xpath[0].click()

    def search_for_target(self):
        """
        search_for_target: perform search action to find target user
        """

        # click on search bar
        ele_one, ele_two = self.get_search_bar_els()
        search = ele_one or ele_two
        search[0].click()
        time.sleep(5)

        # input search query in search bar
        self.input_text_in_search_bar()
        self.driver().press_keycode(66)
        time.sleep(5)

        # click on people tab in search page
        self.click_on_first_tab()
        time.sleep(5)

        # click on comment icon
        ele_one = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/inline_retweet")'
        )
        if ele_one:
            ele_one[0].click()

    def retweet_recent_tweet(self):
        retweet_icon = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/action_sheet_item_icon")')
        time.sleep(3)
        if retweet_icon:
            retweet_icon[0].click()

    def search_for_target_multiple_actions(self, driver, target):
        # click on search bar
        ele_one = self.driver().find_elements_by_xpath('//android.widget.RelativeLayout[@content-desc="Search Twitter"]')
        ele_two = driver().find_elements_by_xpath(
            '//android.widget.RelativeLayout[@content-desc="Search Twitter"]/android.widget.TextView'
        )

        search = ele_one or ele_two
        search[0].click()
        time.sleep(5)

        # input search query in search bar
        search_bar = driver().find_elements_by_xpath('//android.widget.EditText[@content-desc="Search"]')
        search_bar[0].send_keys(str(target))
        press_enter(driver)
        time.sleep(5)

        return True

    @retry()
    def perform_retweet(self, target_name):
        """
        perform_retweet: Performs 'retweet on recent tweet' action.
        """
        try:
            self.target_name = target_name
            restart_app(self.driver, 'twitter')
            self.goto_search()
            self.search_for_target()

            print("retweet recent tweet")
            time.sleep(2)
            self.retweet_recent_tweet()
            return True
        except Exception as e:
            print(e)
            return False

    @retry()
    def search_post_retweet(self):
        restart_app(self.driver, 'twitter')
        self.goto_search()
        time.sleep(5)

        # input search query in search bar
        self.search_for_target_multiple_actions(self.driver, target=self.target_name)
        time.sleep(5)

        return True

    def retweet_searched_tweet(self):
        ele_one = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/inline_retweet")'
        )
        if ele_one:
            ele_one[0].click()

        time.sleep(2)

        retweet_icon = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/action_sheet_item_icon")')
        time.sleep(3)
        if retweet_icon:
            retweet_icon[0].click()