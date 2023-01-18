"""
This file contains all available tweet actions.
"""
import time
import re
from twbot.bot import TwitterBot
from twbot.models import UserAvd
from twbot.utils import *
from ppadb.client import Client as AdbClient
from twbot.basebot import AndroidBaseBot
from appium.webdriver.common.touch_action import TouchAction
from utils import get_tweet
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


class BlankTweetException(Exception):
    """No tweet from tweet API"""

class TweetActionOne:
    """
    algo:
    - Start twitter app
    - Click on home button
    - Click on tweet
    - write over tweet
    - click on tweet button
    - close app
    """

    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name

    def click_on_home_tab(self):
        """
        click_on_home_tab: Clicks on home tab.
        """

        home_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View'
        )
        home_xpath2 = self.driver().find_elements_by_id(
            "com.twitter.android:id/channels"
        )
        ppl_btn = home_xpath1 or home_xpath2
        ppl_btn[0].click()

    def text_tweet(self):
        """
        text tweet
        """
        home_xpath1 = self.driver().find_elements_by_id("com.twitter.android:id/layout")
        home_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.LinearLayout"
        )
        compose_tweet_id = 'com.twitter.android:id/composer_write'
        composer = self.driver().find_elements_by_id(compose_tweet_id)
        

        ppl_btn = home_xpath1 or home_xpath2 or composer
        ppl_btn[0].click()

        # for some versions of twitter, there two layers when clicking composing tweet 
        random_sleep(1, 3)
        composer = self.driver().find_elements_by_id(compose_tweet_id)
        if composer:
            composer[0].click()
            random_sleep(1, 3)

        tweet_text1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/tweet_text"
        )
        tweet_text2 = self.driver().find_elements_by_xpath(
            '//android.widget.FrameLayout[@content-desc="Edit Tweet 1 of 1"]/android.widget.FrameLayout/'
            "android.widget.LinearLayout[1]/android.widget.FrameLayout/android.widget.EditText"
        )
        tweet_text3 = self.driver().find_elements_by_id(
            "com.twitter.android:id/tweet_box"
        )
        tweet_text = tweet_text1 or tweet_text2 or tweet_text3
        tweet_text[0].send_keys(self.text)

        tweet1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/button_tweet"
        )
        tweet2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.view.ViewGroup/android.widget.LinearLayout/android.widget.Button"
        )
        tweet = tweet1 or tweet2
        random_sleep(5, 10)
        tweet[0].click()

    @retry()
    def perform_tweet(self, text):
        """
        perform_tweet: Performs tweet action.
        """

        self.text = text
        #  self.click_on_home_tab()
        goto_home(self.driver)
        self.text_tweet()
        return True


class TweetActionTwo:
    """
    algo:
    - Start twitter app
    - Click on home button
    - Click on tweet
    - click on gallery and select image
    - click on tweet button
    - close app
    """

    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name
        self.adb = AdbClient()

    def click_on_home_tab(self):
        """
        click_on_home_tab: Clicks on home tab.
        """

        home_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View'
        )
        home_xpath2 = self.driver().find_elements_by_id(
            "com.twitter.android:id/channels"
        )
        ppl_btn = home_xpath1 or home_xpath2
        ppl_btn[0].click()

    def select_image(self):
        """
        find image path
        """

        gallery_p1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/gallery_name"
        )
        gallery_p2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/"
            "android.widget.FrameLayout/android.widget.Spinner/android.widget.LinearLayout/android.widget.TextView"
        )
        gallery = gallery_p1 and gallery_p2
        gallery[0].click()

        image_p1 = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("More...")'
        )
        image_p1[0].click()
        roots = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]'
        )
        roots[0].click()
        download = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Downloads")'
        )
        try:
            download[1].click()
        except:
            download[0].click()

    def tweet_image(self):
        """
        tweet image
        """

        home_xpath1 = self.driver().find_elements_by_id("com.twitter.android:id/layout")
        home_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.LinearLayout"
        )
        ppl_btn = home_xpath1 or home_xpath2
        ppl_btn[0].click()
        time.sleep(1)
        gallery1 = self.driver().find_elements_by_id("com.twitter.android:id/gallery")
        gallery2 = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Photos"]'
        )
        gallery = gallery1 or gallery2
        gallery[0].click()
        time.sleep(2)
        self.select_image()
        img1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/"
            "android.widget.LinearLayout/android.widget.RelativeLayout/android.widget.FrameLayout/"
            "android.widget.ImageView[1]"
        )
        img2 = self.driver().find_elements_by_id("com.android.documentsui:id/thumbnail")
        img = img1 or img2
        img[0].click()
        time.sleep(2)
        tweet = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("TWEET")'
        )
        tweet[0].click()

    def push_image_to_device(self):
        """
        push image on device
        """
        self.adb.devices()[0].shell("rm -rf /storage/emulated/0/Download/*")
        self.adb.devices()[0].push(
            self.file_path, "/storage/emulated/0/Download/simple.jpg"
        )
        time.sleep(2)

    def delete_download_files(self):
        """
        delete download files
        """
        self.adb.devices()[0].shell("rm -rf /storage/emulated/0/Download/*")
        return True

    @retry()
    def perform_tweet(self, file_path):
        """
        perform_tweet: Performs tweet action.
        """
        self.file_path = file_path
        self.push_image_to_device()
        self.click_on_home_tab()
        self.tweet_image()
        self.delete_download_files()
        return True


class TweetActionThree:
    """
    algo:
    - Start twitter app
    - Click on home button
    - Click on tweet
    - click on gallery and select image
    - click on tweet button
    - close app
    """

    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name
        self.adb = AdbClient()

    def click_on_home_tab(self):
        """
        click_on_home_tab: Clicks on home tab.
        """

        home_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View'
        )
        home_xpath2 = self.driver().find_elements_by_id(
            "com.twitter.android:id/channels"
        )
        ppl_btn = home_xpath1 or home_xpath2
        ppl_btn[0].click()

    def select_video(self):
        """
        find video path
        """
        gallery_p1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/gallery_name"
        )
        gallery_p2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/"
            "android.widget.FrameLayout/android.widget.Spinner/android.widget.LinearLayout/android.widget.TextView"
        )
        gallery = gallery_p1 and gallery_p2
        gallery[0].click()
        image_p1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ListView/"
            "android.widget.LinearLayout[2]/android.widget.TextView"
        )
        image_p1[0].click()
        roots = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]'
        )
        roots[0].click()

        path = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout[2]/"
            "android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[3]/"
            "android.widget.FrameLayout[1]/android.widget.ImageView"
        )
        path[0].click()
        img1 = self.driver().find_elements_by_id("android:id/title")
        img2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/"
            "android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/"
            "android.widget.TextView"
        )
        img = img1 or img2
        if img:
            img[0].click()

    def tweet_video(self):
        """
        tweet video
        """

        home_xpath1 = self.driver().find_elements_by_id("com.twitter.android:id/layout")
        home_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.LinearLayout"
        )

        ppl_btn = home_xpath1 or home_xpath2
        ppl_btn[0].click()
        time.sleep(1)
        gallery1 = self.driver().find_elements_by_id("com.twitter.android:id/gallery")
        gallery2 = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Photos"]'
        )

        gallery = gallery1 or gallery2
        gallery[0].click()
        time.sleep(2)

        img = self.driver().find_elements_by_xpath(
            '(//android.widget.FrameLayout[@content-desc="Image"])[1]/'
            "android.widget.FrameLayout/android.widget.FrameLayout"
        )
        img[0].click()
        time.sleep(2)
        done1 = self.driver().find_elements_by_id("com.twitter.android:id/done")
        done2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.view.ViewGroup/androidx.appcompat.widget.LinearLayoutCompat/"
            "android.widget.TextView"
        )
        done = done1 or done2
        done[0].click()
        time.sleep(2)
        tweet1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/button_tweet"
        )
        tweet2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.view.ViewGroup/android.widget.LinearLayout/android.widget.Button"
        )
        tweet = tweet1 or tweet2
        tweet[0].click()

    def push_image_to_device(self):
        """
        push image on device
        """
        self.adb.devices()[0].push(self.file_path, "sdcard/Download/simple.mp4")
        self.adb.devices()[0].shell(
            "am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Download/simple.mp4"
        )
        time.sleep(2)

    def delete_download_files(self):
        """
        delete download files
        """
        self.adb.devices()[0].shell("rm -rf sdcard/Download/*")
        return True

    @retry()
    def perform_tweet(self, file_path):
        """
        perform_tweet: Performs tweet action.
        """

        self.file_path = file_path
        restart_app(self.driver, 'twitter')
        self.push_image_to_device()
        self.click_on_home_tab()
        self.tweet_video()
        self.delete_download_files()
        return True


class TweetActionFour:
    """
    algo:
    - Start twitter app
    - Click on home button
    - Click on tweet
    - click on gallery and select image
    - click on tweet button
    - close app
    """

    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name
        self.adb = AdbClient()

    def click_on_home_tab(self):
        """
        click_on_home_tab: Clicks on home tab.
        """

        home_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View'
        )
        home_xpath2 = self.driver().find_elements_by_id(
            "com.twitter.android:id/channels"
        )
        ppl_btn = home_xpath1 or home_xpath2
        ppl_btn[0].click()

    def select_image(self):
        """
        find image path
        """

        gallery_p1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/gallery_name"
        )
        gallery_p2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/"
            "android.widget.FrameLayout/android.widget.Spinner/android.widget.LinearLayout/android.widget.TextView"
        )
        gallery = gallery_p1 and gallery_p2
        gallery[0].click()

        image_p1 = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("More...")'
        )
        image_p1[0].click()
        roots = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]'
        )
        roots[0].click()
        download = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Downloads")'
        )
        try:
            download[1].click()
        except:
            download[0].click()

        dir = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/"
            "android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/"
            "android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
            "android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/"
            "android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/"
            "android.widget.TextView"
        )
        dir[0].click()

    def tweet_image(self):
        """
        tweet image
        """
        for post_img in range(1, self.limit + 1):

            home_xpath1 = self.driver().find_elements_by_id(
                "com.twitter.android:id/layout"
            )
            home_xpath2 = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/"
                "android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/"
                "android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.LinearLayout"
            )
            ppl_btn = home_xpath1 or home_xpath2
            ppl_btn[0].click()
            time.sleep(1)
            gallery1 = self.driver().find_elements_by_id(
                "com.twitter.android:id/gallery"
            )
            gallery2 = self.driver().find_elements_by_xpath(
                '//android.widget.ImageButton[@content-desc="Photos"]'
            )
            gallery = gallery1 or gallery2
            gallery[0].click()
            time.sleep(2)
            self.select_image()
            img_path = f"/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[{post_img}]/android.widget.RelativeLayout/android.widget.FrameLayout/android.widget.ImageView"
            img_dir1 = self.driver().find_elements_by_xpath(img_path)
            img_dir2 = self.driver().find_elements_by_id("android:id/title")
            img_dir = img_dir1 or img_dir2
            if img_dir:
                img_dir[0].click()
                time.sleep(2)

            tweet = self.driver().find_elements_by_android_uiautomator(
                'new UiSelector().text("TWEET")'
            )
            tweet[0].click()
            time.sleep(20)

    def push_image_to_device(self):
        """
        push image on device
        """
        self.adb.devices()[0].shell("rm -rf /storage/emulated/0/Download/*")
        self.adb.devices()[0].push(self.file_path, "/storage/emulated/0/Download")
        time.sleep(2)

    def delete_download_files(self):
        """
        delete download files
        """
        self.adb.devices()[0].shell("rm -rf /storage/emulated/0/Download/*")
        return True

    @retry()
    def perform_tweet(self, file_path, limit):
        """
        perform_tweet: Performs tweet action.
        """
        self.file_path = file_path
        self.limit = limit
        restart_app(self.driver, 'twitter')
        self.push_image_to_device()
        self.click_on_home_tab()
        self.tweet_image()
        self.delete_download_files()
        return True

class Tweet(AndroidBaseBot):

    list_id = 'android:id/list'
    frame_layout_xpath = ('androidx.recyclerview.widget.RecyclerView'
            f'[@resource-id="{list_id}"]/android.widget.FrameLayout')
    list_item_xpath = ('androidx.recyclerview.widget.RecyclerView'
            f'[@resource-id="{list_id}"]/android.view.ViewGroup')
    tweet_container_id = 'com.twitter.android:id/outer_layout_row_view_tweet'
    outer_layout_row_view_tweet_id = (
            'com.twitter.android:id/outer_layout_row_view_tweet')

    tweet_element_id = 'com.twitter.android:id/row'
    tweet_child_element_xpath = (
            f'//android.view.ViewGroup[@resource-id="{tweet_element_id}"]/*')
    tweet_promoted_badge_id = 'com.twitter.android:id/tweet_promoted_badge'
    tweet_promoted_badge_bottom_id = 'com.twitter.android:id/tweet_promoted_badge_bottom'
    social_context_badge_id = 'com.twitter.android:id/social_context_badge'
    social_context_text_id = 'com.twitter.android:id/social_context_text'
    tweet_profile_image_container_id = 'com.twitter.android:id/tweet_profile_image_container'
    tweet_profile_image_id = 'com.twitter.android:id/tweet_profile_image'
    tweet_header_id = 'com.twitter.android:id/tweet_header'
    tweet_curation_action_id = 'com.twitter.android:id/tweet_curation_action'
    tweet_content_text_id = 'com.twitter.android:id/tweet_content_text'
    tweet_content_desc = 'content-desc'

    # promoted tweet
    promoted_tweet_title_id = title_id = 'com.twitter.android:id/title'

    # inline video
    card_media_tweet_container_id = 'com.twitter.android:id/card_media_tweet_container'
    video_player_view_id = 'com.twitter.android:id/video_player_view'
    replay_button_id = 'com.twitter.androud:id/replay_button'
    av_badge_container_id = 'com.twitter.android:id/av_badge_container'
    av_badge_duration_text_id = 'com.twitter.android:id/av_badge_duration_text'
    inflated_video_attribution_id = 'com.twitter.android:id/inflated_video_attribution'
    view_counts_attribution_layout_id = 'com.twitter.android:id/view_counts_attribution_layout'
    view_counts_id = 'com.twitter.android:id/view_counts'

    # inline actions
    tweet_inline_actions_id = 'com.twitter.android:id/tweet_inline_actions'
    inline_reply_id = 'com.twitter.android:id/inline_reply'
    inline_reply_icon_rel_xpath = '//android.widget.FrameLayout[1]/android.widget.ImageView'
    inline_reply_text_rel_xpath = '//android.widget.FrameLayout[2]/android.widget.TextView'
    inline_retweet_id = 'com.twitter.android:id/inline_retweet'
    inline_retweet_icon_rel_xpath = '//android.widget.FrameLayout[1]/android.widget.ImageView'
    inline_retweet_text_rel_xpath = '//android.widget.FrameLayout[2]/android.widget.TextView'
    inline_like_id = 'com.twitter.android:id/inline_like'
    inline_like_icon_rel_xpath = '//android.widget.FrameLayout[1]/android.widget.ImageView'
    inline_like_text_rel_xpath = '//android.widget.FrameLayout[2]/android.widget.TextView'
    inline_twitter_share_id = 'com.twitter.android:id/inline_twitter_share'
    inline_twitter_share_icon_rel_xpath = '//android.widget.FrameLayout[1]/android.widget.ImageView'

    # additional text: show this thread
    tweet_additional_context_text_id = 'com.twitter.android:id/tweet_additional_context_text'

    # tabs in profle: Tweets, Tweets&replies, Media, Likes
    tabs_holder_id = 'com.twitter.android:id/tabs_holder'
    tabs_id = 'com.twitter.android:id/tabs'
    tweets_tab_content_desc = 'Tweets'
    tweets_tab_replies_content_desc = 'Tweets & replies'
    media_tab_content_desc = 'Media'
    likes_tab_content_desc = 'Likes'
    tab_text_rel_xpath = '//android.widget.TextView'    # to get text of every tab

    # profile item list container
    pinned_header_container_id = 'com.twitter.android:id/pinned_header_container'
    profile_header_id = 'com.twitter.android:id/profile_header'
    stats_container_id = 'com.twitter.android:id/stats_container'

    # tweet detail page activity
    tweet_detail_page_activity = '.TweetDetailActivity'

    # tweet detail page
    focal_tweet_container_id = 'com.twitter.android:id/focal_tweet_container'
    # tweet content
    tweet_content_id = 'com.twitter.android:id/tweet_content'
    content_text_id = 'com.twitter.android:id/content_text' # has the content
    card_text_id = 'com.twitter.android:id/card_text'


    timeout = 10

    def __init__(self, driver):
        super().__init__(driver)

    def get_left_blank_area(self, item_element):
        container = item_element.find_element_by_id(
                self.outer_layout_row_view_tweet_id)
        #  tweet_header = item_element.find_element_by_id(
        #          self.tweet_header_id)
        tweet_text = item_element.find_element_by_id(
                self.tweet_content_text_id)
        tweet_image = item_element.find_element_by_id(
                self.tweet_profile_image_id)

        x = container.location['x']
        y = tweet_image.location['y'] + tweet_image.size['height']

        width = tweet_image.size['width']
        height = tweet_image.location['y'] - container.location['y'] 
        area = {'x': x, 'y': y, 'width': width, 'height': height}
        LOGGER.debug(f'Left blank display area: {area}')
        return area

    def click_tweet(self, item_element):
        left_blank_area = self.get_left_blank_area(item_element)
        x = left_blank_area['x']
        y = left_blank_area['y']
        width = left_blank_area['width']
        height = left_blank_area['height']

        middle_x = x + width // 2
        middle_y = y + height // 2
        # click the middle point of left blank area
        action = TouchAction(self.driver)
        action.tap(x=middle_x, y=middle_y).perform()
        LOGGER.debug(f'Cliked the point of left blank area: ({middle_x},'
                f' {middle_y})')

    def is_pinned_tweet(self, element):
        #  if self.find_element_from_parent(element, 'pinned tweet',
        #          self.social_context_badge_id, By.ID):
        #      return element

        try:
            tweet_element = element.find_element_by_id(self.tweet_element_id)
            content = tweet_element.get_attribute('content-desc')
            LOGGER.debug(f'Tweet content: {content}')
        except NoSuchElementException as e:
            LOGGER.error(e)
            return None
        if '. . . Pinned Tweet.' in content:
            LOGGER.debug('Found pinned tweet by content-desc')
            return element

    def is_promoted_tweet(self, element):
        if self.find_element_from_parent(element, 'promoted tweet',
                self.tweet_promoted_badge_id, By.ID):
            return element

        if self.find_element_from_parent(element, 'promoted tweet',
                self.tweet_promoted_badge_bottom_id, By.ID):
            return element

        tweet_element = element.find_element_by_id(self.tweet_element_id)
        content = tweet_element.get_attribute('content-desc')
        LOGGER.debug(f'Tweet content: {content}')
        if '. . . Promoted.' in content:
            LOGGER.debug('Found promoted tweet by content-desc')
            return element

        ele = self.find_element('Tweet flag title',
                self.promoted_tweet_title_id, By.ID, timeout=0)
        if ele:
            if 'Promoted Tweet' in ele.text:
                LOGGER.debug(f'Found promoted tweet by title: {ele.text}')
                return element

    def ignore_pinned_promoted_tweet(self, element):
        flag = False
        ele = self.is_pinned_tweet(element)
        if ele:
            LOGGER.debug('Ignore one pinned tweet')
            self.swipe_element_vertically(ele)
            return True

        ele = self.is_promoted_tweet(driver, element)
        if ele:
            LOGGER.debug('Ignore one promoted tweet')
            self.swipe_element_vertically(ele)
            return True

        return flag

    def exists(self, element):
        if self.find_element_from_parent(element, 'tweet element',
                self.tweet_element_id, By.ID):
            return True
        else:
            return False

    def get_latest_tweet(self, except_tweets=[]):
        LOGGER.debug('Get latest tweet except pinned or promoted one')
        tweet_viewgroup_element_xpath = (
                '//androidx.recyclerview.widget.RecyclerView'
                '[@resource-id="android:id/list"]/android.view.ViewGroup')
        times = 0
        while True:
            #  random_sleep()
            tweet_viewgroup_elements = self.driver.find_elements_by_xpath(
                    tweet_viewgroup_element_xpath)
            if not tweet_viewgroup_elements:
                LOGGER.error('Cannot find tweet ViewGroup element')
                return None

            element = None
            for tweet_viewgroup_element in tweet_viewgroup_elements:
                if not self.check_element_is_tweet_element(
                        tweet_viewgroup_element):
                    continue

                tweet_element = tweet_viewgroup_element.find_element_by_id(
                        self.tweet_element_id)
                if self.is_pinned_tweet(tweet_element) or self.is_promoted_tweet(
                        self.driver, tweet_element):
                    element = tweet_viewgroup_element
                    continue

                content = tweet_element.get_attribute('content-desc')
                #  LOGGER.debug(f'content: {content}')
                p = '(.*( \.){2,})'
                m = re.match(p, content, re.MULTILINE|re.DOTALL)
                if m:
                    effect_content = m[0]
                    if effect_content in except_ids:
                        LOGGER.debug(f'Ignore the element content: {effect_content}')
                        element = tweet_viewgroup_element
                        continue
                    else:
                        return tweet_viewgroup_element
                else:
                    LOGGER.error('Cannot find effective content')

            if element:
                self.swipe_element_vertically(self.driver, element, duration=2000)
            times += 1
            if times > 20:
                LOGGER.error('Some erroe happened, and exit loop')
                break

    def get_item_list(self):
        return self.driver.find_elements_by_id(self.list_item_xpath)

    def check_item_display(self):
        if not self.get_item_list():
            return False
        return True

    def swipe_container_if_no_item(self):
        if not self.check_item_display():
            #  container = self.driver.find_element_by_id(self.pinned_header_container_id)
            profile_header = self.driver.find_element_by_id(self.profile_header_id)
            LOGGER.debug('Swipe list container because no item is displayed')
            self.swipe_element_vertically(profile_header)

    def swipe_profile_header(self):
        profile_header = self.driver.find_element_by_id(self.profile_header_id)
        LOGGER.debug('Swipe profile header')
        self.swipe_element_vertically(profile_header)

    def is_profile_page(self, timeout=timeout):
        """Check if the profile page exists"""
        page = 'Profile'
        profile_header = 'Profile Header'
        stats_container = 'Statistics Container'

        return self.find_page(page=page, element=profile_header,
                locator=self.profile_header_id,
                locator_type=By.ID,
                timeout=timeout) or self.find_page(page=page,
                        element=stats_container,
                        locator=self.stats_container_id,
                        locator_type=By.ID,
                        timeout=timeout)

    def get_inner_tweet_element_from_item(self, item_element):
        tweet_element = item_element.find_element_by_id(
                self.tweet_element_id)
        return tweet_element

    def get_tweet_content_attr(self, tweet_element):
        content = tweet_element.get_attribute(self.tweet_content_desc)
        LOGGER.debug(f'Tweet content as the attribute: {content}')
        return content

    def get_tweet_content_attr_from_item(self, item_element):
        tweet_element = self.get_inner_tweet_element_from_item(item_element)
        return self.get_tweet_content_attr(tweet_element)

    def get_constant_part_from_tweet_content_attr(self, item_element):
        content = self.get_tweet_content_attr_from_item(item_element)
        p = '(.*( \.){2,})' # get the effective content or constant part
        m = re.match(p, content, re.MULTILINE|re.DOTALL)
        if m:
            constant_content = m[0]
            LOGGER.debug('Constant part of tweet content attribute: '
                    f'{constant_content}')
            return constant_content

    def click_tweet_by_header(self, item_element):
        self.click_element('Tweet header', self.tweet_header_id,
                locator_type=By.ID, timeout=0)

    def is_tweet_detail_page(self):
        if self.tweet_detail_page_activity in self.driver.current_activity:
            return True

    def is_tweet_display(self, item_element):
        #  elements = self.find_elements_from_parent(item_element, 'Tweet child elements',
        #          self.tweet_child_element_xpath, locator_type=By.XPATH)
        #  return elements
            #  return True
        tweet_element = item_element.find_element_by_id(self.tweet_element_id)
        child_elements = tweet_element.find_elements_by_xpath('child::*/*')
        return child_elements

    def create_tweet(self, tweet='', form='text', use_api=True):
        try:
            if form == 'text':
                writer = TweetActionOne(self.old_driver, '')
            elif form == 'image':
                writer = TweetActionTwo(self.old_driver, '')
            elif form == 'video':
                writer = TweetActionThree(self.old_driver, '')

            if use_api or tweet == '':
                LOGGER.info('Use tweet API to get tweet')
                tweet = get_tweet()

            if not tweet:
                raise BlankTweetException

            LOGGER.info(f'Create tweet: {tweet}')
            writer.perform_tweet(tweet)
            LOGGER.debug(f'Created the tweet: {tweet}')
            return True
        except Exception as e:
            LOGGER.exception(e)
            return False

    def get_main_tweet_innermost_element(self):
        return self.find_element('Main tweet innermost elements',
                locator=self.focal_tweet_container_id,
                locator_type=By.ID, timeout=self.timeout)

    def get_main_tweet_content(self):
        tweet_element = self.get_main_tweet_innermost_element()
        return self.get_text_from_parent(tweet_element, 'Tweet content',
                locator=self.content_text_id, locator_type=By.ID)

    def get_main_tweet_card_text(self):
        tweet_element = self.get_main_tweet_innermost_element()
        return self.get_text_from_parent(tweet_element, 'Tweet card text',
                locator=self.card_text_id, locator_type=By.ID)

    def get_main_tweet_content_or_card_text(self):
        content = self.get_main_tweet_content()
        if content:
            return content
        text = self.get_main_tweet_card_text()
        return text

class TweetList(AndroidBaseBot):
    # statistics
    stats_container_id = 'com.twitter.android:id/stats_container'
    following_stat_id = 'com.twitter.android:id/following_stat'
    followers_stat_id = 'com.twitter.android:id/followers_stat'
    value_rel_id = 'com.twitter.android:id/value'
    value_text_rel_id = 'com.twitter.android:id/value_text_1'   # text: 434, 1.7M
    name_rel_id = 'com.twitter.android:id/name'     # text: Following, Followers
    text_id = 'com.twitter.android:id/text' # content-desc: Followed by @Google

    # navigate toolbar
    tabs_holder_id = 'com.twitter.android:id/tabs_holder'
    toolbar_id = 'com.twitter.android:id/toolbar'
    navigate_up_content_desc = 'Navigate up'
    more_options_content_desc = 'More options'
    name_rel_xpath = '//android.widget.TextView[1]' # show the name in toolbar, text: CNET
    stats_rel_xpath = '//android.widget.TextView[2]' # show the stats in toolbar, text: 302K Tweets

    # more actions: Share, View Topics, Add/remove from Lists, View Lists,
    # Lists they're on, View Moments, Mute, Block, Report
    more_actions_list_xpath = ('/hierarchy/android.widget.FrameLayout/'
            'android.widget.FrameLayout/android.widget.ListView')
    more_actions_list_item_xpath = (
            '//android.widget.ListView/android.widget.LinearLayout')
    more_actions_item_title_rel_id = 'com.twitter.android:id/title'   # text: Share

    # info list: Tweets, Tweets&replies, Media, Likes
    pinned_header_container_id = 'com.twitter.android:id/pinned_header_container'
    # item list
    list_id = 'android:id/list'
    #  list_item_xpath = ('//androidx.recyclerview.widget.RecyclerView'
    #          f'[@resource-id="{list_id}"]/android.view.ViewGroup')
    list_item_xpath = ('//androidx.recyclerview.widget.RecyclerView'
            f'[@resource-id="{list_id}"]/*')

    # profile page activity: com.twitter.app.profiles.ProfileActivity
    profile_page_activity = '.search.results.SearchActivity'

    # timeout for waiting an element presence
    timeout = 10

    def __init__(self, driver):
        super().__init__(driver)
        self.tweet = Tweet(driver)

    def exists(self, timeout=timeout):
        """Check if the profile page exists"""
        if self.profile_page_activity in self.driver.current_activity:
            return True

    def get_root_element(self):
        return self.find_element('List root element', locator=self.list_id,
                locator_type=By.ID, timeout=self.timeout)

    def get_list_max_display_area(self):
        root_element = self.get_root_element()
        if root_element:
            area = root_element.rect
            LOGGER.debug(f'List max display area: {area}')
            return area

    def swipe_item_top_to_top(self, item_element, delta=20):
        LOGGER.debug('Swipe the element from top of it to the top of list')
        display_area = self.get_list_max_display_area()
        end_y = display_area['y']
        self.swipe_element_vertically(item_element, swipe_from='top',
                end_y=end_y, delta=delta)

    def swipe_item_bottom_to_top(self, item_element, delta=20):
        LOGGER.debug('Swipe the element from bottom of it to the top of list')
        display_area = self.get_list_max_display_area()
        end_y = display_area['y']
        self.swipe_element_vertically(item_element, swipe_from='bottom',
                end_y=end_y, delta=delta)

    def get_item_list(self):
        return self.driver.find_elements_by_xpath(self.list_item_xpath)

    def get_tweet_list(self):
        elements = self.get_item_list()
        #  LOGGER.debug(f'Number of elements: {len(elements)}')
        tweet_elements = []
        for element in elements:
            if self.tweet.exists(element):
                tweet_elements.append(element)

        return tweet_elements

    def click_item(self, item_element):
        pass

    def has_item_list(self, timeout=0):
        if self.find_element('Item list', self.list_id, locator_type=By.ID,
                timeout=timeout):
            if self.get_item_list():
                return True
        return False

    def has_tweet_item_list(self, timeout=0):
        if self.find_element('Item list', self.list_id, locator_type=By.ID,
                timeout=timeout):
            if self.get_tweet_list():
                return True
        return False

    def get_latest_tweet(self, except_tweets=[], find_times=5):
        LOGGER.debug('Get latest tweet except pinned or promoted one')
        times = 0
        retry_times = 0
        max_retries = 30
        while True:
            retry_times += 1
            if retry_times > max_retries:
                LOGGER.warning(f'Number of loops is more than {max_retries}')
                break

            elements = self.get_tweet_list()
            if not elements:
                LOGGER.error('Cannot find tweet elements')
                return None

            try:
                for element in elements:
                    # Ignore pinned or promoted tweet
                    if self.tweet.is_pinned_tweet(element) or (
                            self.tweet.is_promoted_tweet(element)):
                        height = element.size['height']
                        delta = 20
                        LOGGER.debug(f'height: {height}, delta: {delta}')
                        if self.is_item_display(element):
                            #  if height > delta:
                            self.swipe_item_bottom_to_top(element)
                            break
                            #  else:
                            #      continue

                    # check if the tweet is in the except_tweets
                    constant_content = (
                            self.tweet.get_constant_part_from_tweet_content_attr(
                                element))
                    if constant_content:
                        if constant_content in except_tweets:
                            LOGGER.debug('Ignore the element with the content: '
                                    f'{constant_content}')
                            height = element.size['height']
                            delta = 20
                            LOGGER.debug(f'height: {height}, delta: {delta}')
                            if self.is_item_display(element):
                                #  if height > delta:
                                self.swipe_item_bottom_to_top(element)
                                break
                                #  else:
                                #      continue
                        else:
                            self.swipe_item_top_to_top(element)
                            # after swiping, then get the refreshing elements
                            elements = self.get_tweet_list()
                            return self.find_tweet_element_from_content(
                                    elements, constant_content)
                    else:
                        LOGGER.error('Cannot find effective content')
            except StaleElementReferenceException as e:
                LOGGER.debug(e)
                # restart to get tweet list, because the action of swipe may let
                # other element cannot be found, so caused the error below
                # selenium.common.exceptions.StaleElementReferenceException:
                # Message: Cached elements do not exist in DOM anymore
                continue

            times += 1
            if times > find_times:
                LOGGER.info('Some error happened, and exit loop')
                break

    def find_tweet_element_from_content(self, elements, constant_content):
        for element in elements:
            tweet_constant_content = (
                    self.tweet.get_constant_part_from_tweet_content_attr(
                        element))
            if tweet_constant_content == constant_content:
                LOGGER.debug('Found the tweet element from constant content')
                return element

    def is_item_display(self, item_element):
        root_element = self.get_root_element()
        return self.element_part_is_in_view_window(item_element, root_element)

