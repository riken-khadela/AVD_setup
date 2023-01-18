"""
This file contains all available comment actions.
"""
import time

from appium.webdriver.common.touch_action import TouchAction

from twbot.bot import TwitterBot
from twbot.models import UserAvd
from twbot.utils import *


class CommentActionOne:
    """
        algo:
        - Start twitter app
        - Click on search button
        - Click on search bar and type target username
        - Click comment icon of his first tweet
        - Type text message and click on reply button
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

    def _y_scroll(self):
        scroll_dur_ms = 3000
        window_size = self.driver().get_window_size()
        actions = TouchAction(self.driver())
        actions.long_press(None, window_size['width'] * 0.5, window_size['height'] * 0.8, scroll_dur_ms)
        actions.move_to(None, window_size['width'] * 0.5, window_size['height'] * 0.2)
        actions.perform()

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
            'new UiSelector().resourceId("com.twitter.android:id/inline_reply")'
        )
        if ele_one:
            ele_one[0].click()


    def comment_on_recent_tweet(self):

        edit_text = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/tweet_text")'
        )
        time.sleep(3)

        if edit_text:
            edit_text[0].send_keys(str(self.message))

            reply = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/button_tweet")'
            )
            time.sleep(3)
            if reply:
                reply[0].click()
                return True
            else:
                return False
        else:
            return False

    def comment_on_openend_post(self):
        LOGGER.debug('comment for post')
        comment_field_id = self.driver().find_elements_by_id('com.twitter.android:id/tweet_text')
        comment_field_xpath = self.driver().find_elements_by_xpath('/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.EditText')
        comment_field = comment_field_id or comment_field_xpath
        
        if comment_field:
            comment_field[0].click()
            time.sleep(1)
            LOGGER.debug(f'comment: {self.message}')
            comment_field[0].send_keys(self.message)
            time.sleep(1)

            tweet_btn_id = self.driver().find_elements_by_id('com.twitter.android:id/tweet_button')
            tweet_btn_xpath = self.driver().find_elements_by_xpath('/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.FrameLayout[2]/android.widget.LinearLayout[2]/android.widget.Button')
            tweet_btn = tweet_btn_id or tweet_btn_xpath
            tweet_btn[0].click()
            print(f"Successfully commented on {self.target_name}'s latest post.")
            return True
        else:
            print("Couldn't comment: comment field not found.")
            return False

    @retry()
    def perform_comment(self, target_name, message):
        """
        perform_comment: Performs 'comment on recent tweet' action.
        """
        try:
            self.message = message
            self.target_name = target_name
            restart_app(self.driver, 'twitter')
            self.goto_search()
            self.search_for_target()

            print("comment on recent tweet")
            time.sleep(2)
            self.comment_on_recent_tweet()
            return True
        except Exception as e:
            print(e)
            return False


