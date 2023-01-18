import time
from twbot.bot import TwitterBot
from twbot.models import UserAvd
from twbot.utils import *
from ppadb.client import Client as AdbClient
from twbot.basebot import AndroidBaseBot
from twbot.actions.tweet import Tweet
from selenium.common.exceptions import StaleElementReferenceException


class ProfilePage(AndroidBaseBot):
    profile_header_id = 'com.twitter.android:id/profile_header'

    # follow button
    # text: FOLLOWING
    # content-desc: Following CNET. Unfollow.
    # text: FOLLOW
    # content-desc: Follow CNET. Follow.
    button_bar_following_id = 'com.twitter.android:id/button_bar_following'
    # message button
    button_bar_direct_message_container_id = (
            'com.twitter.android:id/button_bar_direct_message_container')

    # Unfollow
    alertTitle_id = 'android:id/alertTitle' # text: Unfollow
    message_id = 'android:id/message'   # text: Stop following CNET?
    button2_id = 'android:id/button2'   # text: NO
    button1_id = 'android:id/button1'   # text: YES

    # profile info
    name_id = 'com.twitter.android:id/name'
    user_name_id = 'com.twitter.android:id/user_name'
    profile_user_details_id = 'com.twitter.android:id/profile_user_details'
    user_bio_id = 'com.twitter.android:id/user_bio' # content-desc & text include bio
    icon_items_container_id = 'com.twitter.android:id/icon_items_container'
    address_rel_xpath = '//android.widget.TextView[1]'
    url_rel_xpath = '//android.widget.TextView[2]'
    join_time_rel_xpath = '//android.widget.TextView[3]'

    # statistics
    stats_container_id = 'com.twitter.android:id/stats_container'
    following_stat_id = 'com.twitter.android:id/following_stat'
    followers_stat_id = 'com.twitter.android:id/followers_stat'
    value_rel_id = 'com.twitter.android:id/value'
    value_text_rel_id = 'com.twitter.android:id/value_text_1'   # text: 434, 1.7M
    name_rel_id = 'com.twitter.android:id/name'     # text: Following, Followers

    # Followd by @Google
    profile_social_proof_id = 'com.twitter.android:id/profile_social_proof'
    social_proof_container_id = 'com.twitter.android:id/social_proof_container'
    social_proof_face_pile_id = 'com.twitter.android:id/social_proof_face_pile'
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
    profile_page_activity = '.profiles.ProfileActivity'

    # timeout for waiting an element presence
    timeout = 10

    def __init__(self, driver):
        super().__init__(driver)
        self.tweet = Tweet(driver)

    def exists(self, timeout=timeout):
        """Check if the profile page exists"""
        #  page = 'Profile'
        #  profile_header = 'Profile Header'
        #  stats_container = 'Statistics Container'
        #
        #  return self.find_page(page=page, element=profile_header,
        #          locator=self.profile_header_id,
        #          locator_type=By.ID,
        #          timeout=timeout) or self.find_page(page=page,
        #                  element=stats_container,
        #                  locator=self.stats_container_id,
        #                  locator_type=By.ID,
        #                  timeout=timeout)
        if self.profile_page_activity in self.driver.current_activity:
            return True

    def pull_down_refresh(self):
        """Pull down from toolbar to bottom"""
        pass

    def get_list_max_display_area(self):
        container = self.driver.find_element_by_id(
                self.pinned_header_container_id)
        tabs_holder = self.driver.find_element_by_id(
                self.tabs_holder_id)

        width = container.size['width']
        height = container.size['height'] - tabs_holder.size['height']
        x = container.location['x']
        y = container.location['y'] + tabs_holder.size['height']
        area = {'x': x, 'y': y, 'width': width, 'height': height}
        LOGGER.debug(f'List container rect: {container.rect}')
        LOGGER.debug(f'tabs_holder rect: {tabs_holder.rect}')
        LOGGER.debug(f'List max display area: {area}')
        return area

    def swipe_item_top_to_top(self, item_element):
        LOGGER.debug('Swipe the element from top of it to the top of list')
        display_area = self.get_list_max_display_area()
        end_y = display_area['y']
        self.swipe_element_vertically(item_element, swipe_from='top',
                end_y=end_y)

    def swipe_item_bottom_to_top(self, item_element):
        LOGGER.debug('Swipe the element from bottom of it to the top of list')
        display_area = self.get_list_max_display_area()
        end_y = display_area['y']
        self.swipe_element_vertically(item_element, swipe_from='bottom',
                end_y=end_y)

    def get_item_list(self):
        return self.driver.find_elements_by_xpath(self.list_item_xpath)

    def get_tweet_list(self):
        elements = self.get_item_list()
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

    def swipe_profile_header_if_no_item_list(self):
        if not self.has_item_list():
            self.swipe_profile_header()

    def swipe_profile_header_if_no_tweet_item_list(self):
        if not self.has_tweet_item_list():
            self.swipe_profile_header()

    def swipe_profile_header(self):
        profile_header = self.driver.find_element_by_id(self.profile_header_id)
        LOGGER.debug('Swipe profile header from bottom to top')
        self.swipe_element_vertically(profile_header)

    def get_latest_tweet(self, except_tweets=[], find_times=5):
        LOGGER.debug('Get latest tweet except pinned or promoted one')
        times = 0
        while True:
            elements = self.get_tweet_list()
            if not elements:
                LOGGER.error('Cannot find tweet elements')
                return None

            try:
                for element in elements:
                    # Ignore pinned or promoted tweet
                    if self.tweet.is_pinned_tweet(element) or (
                            self.tweet.is_promoted_tweet(element)):
                        if self.is_item_display(element):
                            self.swipe_item_bottom_to_top(element)
                        continue

                    # check if the tweet is in the except_tweets
                    constant_content = (
                            self.tweet.get_constant_part_from_tweet_content_attr(
                                element))
                    if constant_content:
                        if constant_content in except_tweets:
                            LOGGER.debug('Ignore the element with the content: '
                                    f'{constant_content}')
                            if self.is_item_display(element):
                                self.swipe_item_bottom_to_top(element)
                            continue
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
        list_display_area = self.get_list_max_display_area()
        class C: pass
        simulated_view_element = C
        C.rect = list_display_area
        return self.element_part_is_in_view_window(item_element,
                simulated_view_element)
