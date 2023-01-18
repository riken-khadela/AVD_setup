import time
import re
import traceback

from constants import *
from twbot.actions.like import *
from twbot.actions.follow import *
from twbot.actions.comment import *
from twbot.actions.retweet import *
from twbot.actions.tweet import Tweet
from twbot.actions.profile import ProfilePage
from twbot.utils import random_sleep
from selenium.common.exceptions import InvalidElementStateException

from main import LOGGER
from accounts_conf import NEW_POST_EXTERNAL_USER_NAMES, NEW_POST_EXTERNAL_USER_NAMES_NUMBER
from accounts_conf import FOLLOW_OTHER_ACCOUNTS
from twbot.models import (ActionType, ActionForBotAccount,
                          ActionForOtherAccount, ActionForTargetAccount, ActionResult)
from twbot.models import (TwitterAccount, TwitterTargetAccount,
                          TwitterOtherAccount)
from twbot.basebot import AndroidBaseBot
from utils import get_comment
from twbot.utils import get_comment_from_db
from conf import ACCESS_TIMEOUT_FOR_API_SERVER
from twbot.report import (check_comment_number_this_week,
        check_like_number_this_week, check_retweet_number_this_week)


class LikeComment():
    def __init__(self, bot_instance, target_name, comment):
        self.bot = bot_instance
        self.avd_name = self.user_avd.name
        self.avd_port = self.user_avd.port
        self.target_name = target_name
        self.comment = comment

    def get_like_bot(self):
        like_bot = LikeActions(self.avd_name, self.target_name)
        return like_bot

    def get_comment_bot(self):
        comment_bot = CommentActionOne(self.user_avd.id, self.target_name)
        return comment_bot

    def perform_action(self):
        try:
            like_bot = self.get_like_bot()
            like_resp = like_bot.like_latest_post()
            print(like_resp)
            like_bot.service.stop()

            comment_bot = self.get_comment_bot()
            comment_bot.message = self.comment
            comment_bot.comment_on_openend_post()
            comment_bot.service.stop()

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)


class FollowLike():
    def __init__(self, avd_name, target_name):
        self.user_avd = UserAvd.objects.get(name=avd_name)
        self.avd_name = self.user_avd.name
        self.avd_port = self.user_avd.port
        self.target_name = target_name

    def get_like_bot(self):
        like_bot = LikeActions(self.avd_name, self.target_name)
        return like_bot

    def get_follow_bot(self):
        follow_bot = DirectFollow(self.user_avd.id)
        return follow_bot

    def perform_action(self):
        try:
            follow_bot = self.get_follow_bot()
            follow_bot.target_name = self.target_name
            restart_app(follow_bot.driver, 'twitter')
            follow_bot.goto_search()
            follow_bot.search_for_target()
            follow_bot.follow_user()
            follow_bot.service.stop()

            like_bot = self.get_like_bot()
            like_bot.open_latest_post()
            like_resp = like_bot.like_opened_post()
            print(like_resp)
            like_bot.service.stop()

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)


class FollowLikeComment():
    def __init__(self, bot_instance, target_name, comment=None, do_follow=True, do_like=True, do_comment=True,
                 do_retweet=True, total_posts=0, required_likes=0):
        self.perform_retweet = do_retweet
        self.perform_comment = do_comment
        self.perform_follow = do_follow
        self.target_name = target_name
        self.perform_like = do_like
        self.comment = None
        self.bot = bot_instance
        self.like_completed = False
        self.follow_completed = False
        self.comment_completed = False
        self.retweet_completed = False
        self.total_posts = total_posts
        self.required_likes = required_likes

        if do_comment:
            self.comment = random.choice(XANALIA_COMMENTS)

    def perform_action(self):
        try:
            driver = self.bot.driver

            # Open target profile
            restart_app(driver, 'twitter')
            goto_search(driver)
            search_for_target(driver, self.target_name)

            # Perform FOLLOW action
            if self.perform_follow:
                if not self.follow_completed:
                    follow_bot = DirectFollow(driver, self.target_name)
                    follow_resp = follow_bot.follow_user()
                    if follow_resp:
                        TwitterActionLog.objects.create(
                            avd=UserAvd.objects.get(name=self.bot.emulator_name),
                            action_type='FOLLOW',
                            action=follow_resp,
                            status='SUCCESS',
                            error={'msg': ''}
                        )
                        self.follow_completed = True

            # Open latest post on target account
            like_bot = LikeActions(driver, self.target_name)
            for x in range(3):
                if like_bot.open_conditional_post(self.total_posts, self.required_likes):
                    break
                else:
                    tweets_access_id = driver().find_elements_by_accessibility_id('Tweets')
                    tweets_btn_xpath = driver().find_elements_by_xpath(
                        '//android.widget.LinearLayout[@content-desc="Tweets"]')
                    tweets_btn = tweets_access_id or tweets_btn_xpath
                    if tweets_btn:
                        tweets_btn[0].click()
                time.sleep(2)

            # Perform LIKE action
            if self.perform_like:
                if not self.like_completed:
                    like_resp = like_bot.like_opened_post()
                    print(like_resp)
                    if like_resp:
                        self.like_completed = True
                        TwitterActionLog.objects.create(
                            avd=UserAvd.objects.get(name=self.bot.emulator_name),
                            action_type='LIKE',
                            action=like_resp,
                            status='SUCCESS',
                            error={'msg': ''}
                        )
                    if not like_resp:
                        self.like_completed = False

            # Retweet opened tweet
            if self.perform_retweet:
                if not self.retweet_completed:
                    try:
                        retweet_acc_id = driver().find_elements_by_accessibility_id('Retweet')
                        retweet_id = driver().find_elements_by_id('com.twitter.android:id/retweet')
                        retweet_xpath = driver().find_elements_by_xpath(
                            '//android.widget.ImageButton[@content-desc="Retweet"]')
                        retweet_btn = retweet_acc_id or retweet_id or retweet_xpath
                        if retweet_btn:
                            if 'retweeted' not in retweet_btn[0].get_attribute('content-desc').lower():
                                retweet_btn[0].click()
                                time.sleep(2)
                                confirm_retweet_btn_xpath1 = driver().find_elements_by_xpath(
                                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]')
                                confirm_retweet_btn_xpath2 = driver().find_elements_by_xpath(
                                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.widget.TextView')
                                confirm_retweet_btn = confirm_retweet_btn_xpath2 or confirm_retweet_btn_xpath1
                                if confirm_retweet_btn:
                                    confirm_retweet_btn[0].click()
                                    time.sleep(2)
                                    self.retweet_completed = True
                                    print("Successfully retweeted post.")
                                    TwitterActionLog.objects.create(
                                        avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                        action_type='RETWEET_ACTION',
                                        action='Successfully retweeted post.',
                                        status='SUCCESS',
                                        error={'msg': ''}
                                    )
                            else:
                                self.retweet_completed = False
                                print("Post is already retweeted.")
                                TwitterActionLog.objects.create(
                                    avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                    action_type='RETWEET_ACTION',
                                    action='Post is already retweeted.',
                                    status='SUCCESS',
                                    error={'msg': ''}
                                )
                    except:
                        tb = traceback.format_exc()
                        print("There was an error, while retweeting the post.")
                        self.retweet_completed = False

            # Perform COMMENT action
            if self.perform_comment:
                if not self.comment_completed:
                    comment_bot = CommentActionOne(driver, self.target_name)
                    comment_bot.message = self.comment
                    comment_resp = comment_bot.comment_on_openend_post()
                    if comment_resp:
                        self.comment_completed = True
                        TwitterActionLog.objects.create(
                            avd=UserAvd.objects.get(name=self.bot.emulator_name),
                            action_type='COMMENT',
                            action=comment_resp,
                            status='SUCCESS',
                            error={'msg': ''}
                        )

        except Exception as e:
            tb = traceback.format_exc()
            print(f"Something went wrong while performing action on bot {self.bot.emulator_name}")
            print("Error in Action ===============\n", tb)
            TwitterActionLog.objects.create(
                avd=UserAvd.objects.get(name=self.bot.emulator_name),
                action_type='ENGAGEMENT',
                action=comment_resp,
                status='FAIL',
                error={'msg': str(tb)}
            )


class FollowLikeCommentWithLink:
    def __init__(self, bot_instance, post_url, comment=None, do_follow=True,
                 do_like=True, do_comment=True, do_retweet=True, user_name=None):
        self.perform_retweet = do_retweet
        self.perform_comment = do_comment
        self.perform_follow = do_follow
        self.perform_like = do_like
        self.comment = None
        self.bot = bot_instance
        self.like_completed = False
        self.follow_completed = False
        self.comment_completed = False
        self.retweet_completed = False
        self.post_url = post_url
        self.user_name = user_name

        self.driver = self.bot.driver
        self.recorder = Recorder(self.driver)
        self.owner = bot_instance.user_avd.twitter_account

        LOGGER.debug(f'do_comment: {do_comment}')
        if do_comment:
            self.comment = random.choice(COMMENTS)

    def follow_with_link(self, is_post_link=True):
        """follow the owner of this link.

        The link type: post link or user profile link.
        """
        LOGGER.debug('follow with link')
        try:
            # Open URL
            try:
                LOGGER.debug(f'Open this post from webview: {self.post_url}')
                start_app(self.driver, 'webview')
                search_field_id = self.driver().find_elements_by_id('org.chromium.webview_shell:id/url_field')
                search_field_xpath = self.driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout[2]/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.EditText')
                search_field = search_field_id or search_field_xpath
                if search_field[0]:
                    search_field[0].clear()
                    search_field[0].send_keys(self.post_url)
                    time.sleep(3)
                    load_url_btn = self.driver(
                    ).find_elements_by_accessibility_id('Load URL')
                    load_url_btn1 = self.driver().find_elements_by_xpath(
                        '//android.widget.ImageButton[@content-desc="Load URL"]')
                    load_url_btn = load_url_btn or load_url_btn1
                    if load_url_btn:
                        LOGGER.debug('click button "Go" of webview')
                        load_url_btn[0].click()
                        random_sleep(5, 10)
                    self.driver().press_keycode(66)

                else:
                    print("Couldn't open post.")
                    return False, False, False, False
            except:
                return False, False, False, False

            #  time.sleep(3)
            random_sleep()

            # check if it asks for which app to open
            LOGGER.debug('check if it asks for which app to open')
            try:
                title_id = self.driver().find_elements_by_id('android:id/title')
                title_xpath = self.driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.RelativeLayout/android.widget.TextView')
                title = title_id or title_xpath
                if title:
                    if 'open with' in title[0].text.lower():
                        twitter_btn_xpath = self.driver().find_elements_by_xpath(
                            '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.ListView/android.widget.LinearLayout[1]')
                        if twitter_btn_xpath:
                            twitter_btn_xpath[0].click()
                            time.sleep(1)
                            always_id = self.driver().find_elements_by_id('android:id/button_always')
                            always_xpath = self.driver().find_elements_by_xpath(
                                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[2]')
                            always_btn = always_id or always_xpath
                            if always_btn:
                                always_btn[0].click()
            except:
                print("Something went wrong while selecting twitter as default app.")
                return False, False, False, False

            # wait for app to open
            #  time.sleep(10)
            if hasattr(self.driver, '__self__') and hasattr(self.driver.__self__, 'wait_obj'):
                LOGGER.debug('Waiting for twitter')
                locator_type = By.ID
                element_locator = 'com.twitter.android:id/action_bar_root'
                try:
                    element = self.driver.__self__.wait_obj.until(EC.presence_of_element_located(
                        (locator_type, element_locator)))
                except Exception as e:
                    LOGGER.exception(e)
            else:
                random_sleep(10, 20)

            # if the link is profile link, don't open profile.
            # if use the below code to open profile, it dose not work
            if is_post_link:
                # Open Profile
                LOGGER.debug('Open Profile')
                try:
                    profile_btn_id_1 = self.driver().find_elements_by_id('com.twitter.android:id/name')
                    profile_btn_id_2 = self.driver().find_elements_by_id('com.twitter.android:id/screen_name')
                    profile_btn = profile_btn_id_1 or profile_btn_id_2
                    LOGGER.debug(f'click profile_btn: {profile_btn[0]}')
                    profile_btn[0].click()
                    #  time.sleep(5)
                    random_sleep()
                except:
                    print("Couldn't open profile.")
                    return False, False, False, False

            # Perform FOLLOW action
            LOGGER.debug(f'Perform FOLLOW action: {self.perform_follow}')
            if self.perform_follow:
                if not self.follow_completed:
                    try:
                        follow_bot = DirectFollow(self.driver, "")
                        follow_resp = follow_bot.follow_user()
                        LOGGER.debug(f'follow_resp: {follow_resp}')
                        if follow_resp:
                            TwitterActionLog.objects.create(
                                avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                action_type='FOLLOW',
                                action=follow_resp,
                                status='SUCCESS',
                                error={'msg': ''}
                            )
                            self.follow_completed = True
                            # record action info
                            self.recorder.record_action(
                                self.owner,
                                ActionType.FOLLOW_ACCOUNT,
                                self.user_name,
                                ActionResult.SUCCESSFUL)
                    except Exception as e:
                        LOGGER.exception(e)
                        self.follow_completed = False
            else:
                self.follow_completed = True

            self.driver().press_keycode(4)

            # Perform LIKE action
            LOGGER.debug(f'Perform LIKE action: {self.perform_like}')
            if self.perform_like:
                if not self.like_completed:
                    try:
                        like_bot = LikeActions(self.driver, "")
                        like_resp = like_bot.like_opened_post()
                        print(like_resp)
                        if like_resp:
                            self.like_completed = True
                            TwitterActionLog.objects.create(
                                avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                action_type='LIKE',
                                action=like_resp,
                                status='SUCCESS',
                                error={'msg': ''}
                            )
                            # record action info
                            self.recorder.record_action(
                                self.owner,
                                ActionType.LIKE_TWEET,
                                self.user_name,
                                ActionResult.SUCCESSFUL)
                        if not like_resp:
                            self.like_completed = False
                    except:
                        self.like_completed = False
            else:
                self.like_completed = True

            # Retweet opened tweet
            LOGGER.debug(f'Retweet opened tweet: {self.perform_retweet}')
            if self.perform_retweet:
                if not self.retweet_completed:
                    try:
                        retweet_acc_id = self.driver().find_elements_by_accessibility_id('Retweet')
                        retweet_id = self.driver().find_elements_by_id('com.twitter.android:id/retweet')
                        retweet_xpath = self.driver().find_elements_by_xpath(
                            '//android.widget.ImageButton[@content-desc="Retweet"]')
                        retweet_btn = retweet_acc_id or retweet_id or retweet_xpath
                        if retweet_btn:
                            if 'retweeted' not in retweet_btn[0].get_attribute('content-desc').lower():
                                retweet_btn[0].click()
                                time.sleep(2)
                                confirm_retweet_btn_xpath1 = self.driver().find_elements_by_xpath(
                                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]')
                                confirm_retweet_btn_xpath2 = self.driver().find_elements_by_xpath(
                                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.widget.TextView')
                                confirm_retweet_btn = confirm_retweet_btn_xpath2 or confirm_retweet_btn_xpath1
                                if confirm_retweet_btn:
                                    confirm_retweet_btn[0].click()
                                    time.sleep(2)
                                    self.retweet_completed = True
                                    print("Successfully retweeted post.")
                                    TwitterActionLog.objects.create(
                                        avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                        action_type='RETWEET_ACTION',
                                        action='Successfully retweeted post.',
                                        status='SUCCESS',
                                        error={'msg': ''}
                                    )
                                    # record action info
                                    self.recorder.record_action(
                                        self.owner,
                                        ActionType.RETWEET_TWEET,
                                        self.user_name,
                                        ActionResult.SUCCESSFUL)
                            else:
                                self.retweet_completed = False
                                print("Post is already retweeted.")
                                TwitterActionLog.objects.create(
                                    avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                    action_type='RETWEET_ACTION',
                                    action='Post is already retweeted.',
                                    status='SUCCESS',
                                    error={'msg': ''}
                                )
                    except:
                        tb = traceback.format_exc()
                        print("There was an error, while retweeting the post.")
                        self.retweet_completed = False
            else:
                self.retweet_completed = True

            # Perform COMMENT action
            LOGGER.debug(f'Perform COMMENT action: {self.perform_comment}')
            if self.perform_comment:
                if not self.comment_completed:
                    try:
                        comment_bot = CommentActionOne(self.driver, "")
                        comment_bot.message = self.comment
                        comment_resp = comment_bot.comment_on_openend_post()
                        if comment_resp:
                            self.comment_completed = True
                            TwitterActionLog.objects.create(
                                avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                action_type='COMMENT',
                                action=comment_resp,
                                status='SUCCESS',
                                error={'msg': ''}
                            )
                            # record action info
                            self.recorder.record_action(
                                self.owner,
                                ActionType.COMMENT_TWEET,
                                self.user_name,
                                ActionResult.SUCCESSFUL)
                        else:
                            self.comment_completed = False
                    except:
                        self.comment_completed = False
            else:
                self.comment_completed = True

            random_sleep()

        except Exception as e:
            LOGGER.exception(e)
            tb = traceback.format_exc()
            print(f"Something went wrong while performing action on bot {self.bot.emulator_name}")
            print("Error in Action ===============\n", tb)
            TwitterActionLog.objects.create(
                avd=UserAvd.objects.get(name=self.bot.emulator_name),
                action_type='ENGAGEMENT',
                action=comment_resp,
                status='FAIL',
                error={'msg': str(tb)}
            )

        return True

    def perform_action(self):
        top_accs = random.choices(TOP_ACCS, k=random.randrange(1, 4))

        xanalia_turn = random.randrange(0, len(top_accs))

        for index, top_acc in enumerate(top_accs, 0):

            if index == xanalia_turn:
                self.follow_with_link()
            else:
                self.target_name = top_acc
                # Open target profile
                restart_app(self.driver, 'twitter')
                goto_search(self.driver)
                search_for_target(self.driver, self.target_name)

                follow_bot = DirectFollow(self.driver, "")
                follow_resp = follow_bot.follow_user(random_acc=True)
                del follow_bot

        return self.like_completed, self.follow_completed, self.comment_completed, self.retweet_completed


class FollowLikeCommentByUserName:
    def __init__(self, bot_instance, user_name, comment=None, do_follow=True, do_like=True, do_comment=True,
                 do_retweet=True, use_comment_api=True):
        self.perform_retweet = do_retweet
        self.perform_comment = do_comment
        self.perform_follow = do_follow
        self.perform_like = do_like
        self.comment = None
        self.bot = bot_instance
        self.like_completed = False
        self.follow_completed = False
        self.comment_completed = False
        self.retweet_completed = False
        self.post_url = f"twitter.com/{user_name}"
        self.driver = self.bot.driver
        self.user_name = user_name
        self.profile = ProfilePage(self.driver)
        self.recorder = Recorder(self.driver)
        self.owner = bot_instance.user_avd.twitter_account
        self.use_comment_api = use_comment_api

        if do_comment:
            self.comment = random.choice(COMMENTS)

    def do_actions(self, except_tweets=[]):
        try:
            if not except_tweets:
                # Open URL
                try:
                    result = open_profile_by_search(self.user_name, self.driver)
                    if not result:
                        raise Exception('Cannot open profile')
                except Exception as e:
                    LOGGER.exception(e)
                    return False, False, False, False

                random_sleep()

                # Perform FOLLOW action
                if self.perform_follow:
                    LOGGER.debug('Perform FOLLOW action')
                    if not self.follow_completed:
                        try:
                            follow_bot = DirectFollow(self.driver, "")
                            follow_resp = follow_bot.follow_user()
                            if follow_resp:
                                # record action info
                                self.recorder.record_action(
                                    self.owner,
                                    ActionType.FOLLOW_ACCOUNT,
                                    self.user_name,
                                    ActionResult.SUCCESSFUL)

                                TwitterActionLog.objects.create(
                                    avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                    action_type='FOLLOW',
                                    action=follow_resp,
                                    status='SUCCESS',
                                    error={'msg': ''}
                                )
                                self.follow_completed = True
                            else:
                                # record action info
                                self.recorder.record_action(
                                    self.owner,
                                    ActionType.FOLLOW_ACCOUNT,
                                    self.user_name,
                                    ActionResult.FAILED)
                        except Exception as e:
                            LOGGER.exception(e)
                            self.follow_completed = False
                            # record action info
                            self.recorder.record_action(
                                self.owner,
                                ActionType.FOLLOW_ACCOUNT,
                                self.user_name,
                                ActionResult.FAILED)
                else:
                    self.follow_completed = True
            # User Tweets
            #  user_tweets = self.driver().find_elements_by_id("com.twitter.android:id/row")

            if not except_tweets:
                click_suggested_follows_close_button(self.driver)
                self.profile.swipe_profile_header_if_no_tweet_item_list()
            #  tweet = get_latest_tweet(self.driver)
            #  tweet = get_latest_tweet_by_viewgroup(self.driver, except_tweets)
            tweet = self.profile.get_latest_tweet(except_tweets)
            user_tweets = [tweet] if tweet else []
            if user_tweets:
                constant_content = (
                    self.profile.tweet.get_constant_part_from_tweet_content_attr(tweet)
                )
                # click the tweet header, or it will open the url within tweet
                #  user_tweets[0].click()
                self.profile.tweet.click_tweet_by_header(user_tweets[0])
                time.sleep(5)

                # Save the tweet content into DB if the user is the target account
                try:
                    target_users = [
                            e.lower() for e in NEW_POST_EXTERNAL_USER_NAMES]
                    if self.user_name.lower() in target_users:
                        tweet_obj = Tweet(self.driver())
                        tweet_content = (
                                tweet_obj.get_main_tweet_content_or_card_text())
                        LOGGER.debug(f'tweet_content: {tweet_content}')

                        tweet_owner, created = (
                                TwitterTargetAccount.objects.get_or_create(
                                    screen_name=self.user_name))
                        tweet_record, created = (
                                TweetForTargetAccount.objects.get_or_create(
                                    owner=tweet_owner, text=tweet_content))
                        if created:
                            LOGGER.debug(f'Created a record of tweet for target'
                                    f' account: {self.user_name}')
                        else:
                            LOGGER.debug(f'Got a record of tweet for target'
                                    f' account: {self.user_name}')
                    else:
                        LOGGER.debug(f'User {self.user_name} is not in'
                                ' NEW_POST_EXTERNAL_USER_NAMES')
                        tweet_content = ''
                        tweet_record = None
                except Exception as e:
                    LOGGER.error(e)
                    LOGGER.error('Cannot save the tweet for target account:'
                            f' {self.user_name}')
                    tweet_content = ''
                    tweet_record = None

                # check the comment number in db
                #  result = check_comment_number_this_week(
                #          target_user=self.user_name,
                #          tweet_content=tweet_content)
                #  if result:
                #      LOGGER.info('Do nothing for comment action')
                #      self.perform_comment = False

                # Perform COMMENT action
                if self.perform_comment:
                    LOGGER.debug('Perform COMMENT action')
                    if not self.comment_completed:
                        try:
                            comment_bot = CommentActionOne(self.driver, "")
                            # get tweet content
                            if self.use_comment_api:
                                if not tweet_content:
                                    tweet_obj = Tweet(self.driver())
                                    tweet_content = tweet_obj.get_main_tweet_content_or_card_text()
                                    LOGGER.debug(f'tweet_content: {tweet_content}')

                                if tweet_content:
                                    #  comment_bot.message = get_comment(tweet_content)
                                    comment_bot.message = get_comment_from_db(
                                            tweet_content,
                                            timeout=ACCESS_TIMEOUT_FOR_API_SERVER)
                                else:
                                    comment_bot.message = None
                            else:
                                comment_bot.message = self.comment

                            if not comment_bot.message:
                                LOGGER.error('There is no tweet content in this tweet')
                                self.comment_completed = True
                                # record action info
                                self.recorder.record_action(
                                        self.owner,
                                        ActionType.COMMENT_TWEET,
                                        self.user_name,
                                        ActionResult.FAILED,
                                        tweet=tweet_record)
                            else:
                                comment_resp = comment_bot.comment_on_openend_post()
                                time.sleep(5)
                                if comment_resp:
                                    self.comment_completed = True
                                    TwitterActionLog.objects.create(
                                        avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                        action_type='COMMENT',
                                        action=comment_resp,
                                        status='SUCCESS',
                                        error={'msg': ''}
                                    )
                                    # record action info
                                    self.recorder.record_action(
                                            self.owner,
                                            ActionType.COMMENT_TWEET,
                                            self.user_name,
                                            ActionResult.SUCCESSFUL,
                                            tweet=tweet_record)
                                else:
                                    self.comment_completed = False
                                    # record action info
                                    self.recorder.record_action(
                                            self.owner,
                                            ActionType.COMMENT_TWEET,
                                            self.user_name,
                                            ActionResult.FAILED,
                                            tweet=tweet_record)
                        except Exception as e:
                            LOGGER.exception(e)
                            self.comment_completed = False
                            # record action info
                            self.recorder.record_action(
                                    self.owner,
                                    ActionType.COMMENT_TWEET,
                                    self.user_name,
                                    ActionResult.FAILED,
                                    tweet=tweet_record)
                else:
                    self.comment_completed = True

                # check the like number in db
                #  result = check_like_number_this_week(
                #          target_user=self.user_name,
                #          tweet_content=tweet_content)
                #  if result:
                #      LOGGER.info('Do nothing for like action')
                #      self.perform_like = False

                # Perform LIKE action
                if self.perform_like:
                    LOGGER.debug('Perform LIKE action')
                    if not self.like_completed:
                        try:
                            like_bot = LikeActions(self.driver, "")
                            like_resp = like_bot.like_opened_post()
                            time.sleep(5)
                            print(like_resp)
                            if like_resp:
                                # record action info
                                self.recorder.record_action(
                                    self.owner,
                                    ActionType.LIKE_TWEET,
                                    self.user_name,
                                    ActionResult.SUCCESSFUL,
                                    tweet=tweet_record)

                                self.like_completed = True
                                TwitterActionLog.objects.create(
                                    avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                    action_type='LIKE',
                                    action=like_resp,
                                    status='SUCCESS',
                                    error={'msg': ''}
                                )
                            else:
                                # record action info
                                self.recorder.record_action(
                                    self.owner,
                                    ActionType.LIKE_TWEET,
                                    self.user_name,
                                    ActionResult.FAILED,
                                    tweet=tweet_record)
                            if not like_resp:
                                self.like_completed = False
                        except Exception as e:
                            LOGGER.exception(e)
                            self.like_completed = False
                            # record action info
                            self.recorder.record_action(
                                self.owner,
                                ActionType.LIKE_TWEET,
                                self.user_name,
                                ActionResult.FAILED,
                                tweet=tweet_record)
                else:
                    self.like_completed = True

                # check the retweet number in db
                #  result = check_retweet_number_this_week(
                #          target_user=self.user_name,
                #          tweet_content=tweet_content)
                #  if result:
                #      LOGGER.info('Do nothing for retweet action')
                #      self.perform_retweet = False

                # Retweet opened tweet
                if self.perform_retweet:
                    LOGGER.debug('Retweet opened tweet')
                    if not self.retweet_completed:
                        try:
                            retweet_acc_id = self.driver().find_elements_by_accessibility_id('Retweet')
                            retweet_id = self.driver().find_elements_by_id('com.twitter.android:id/retweet')
                            retweet_xpath = self.driver().find_elements_by_xpath(
                                '//android.widget.ImageButton[@content-desc="Retweet"]')
                            retweet_btn = retweet_acc_id or retweet_id or retweet_xpath
                            if retweet_btn:
                                if 'retweeted' not in retweet_btn[0].get_attribute('content-desc').lower():
                                    retweet_btn[0].click()
                                    time.sleep(2)
                                    confirm_retweet_btn_xpath1 = self.driver().find_elements_by_xpath(
                                        '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]')
                                    confirm_retweet_btn_xpath2 = self.driver().find_elements_by_xpath(
                                        '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.widget.TextView')
                                    confirm_retweet_btn = confirm_retweet_btn_xpath2 or confirm_retweet_btn_xpath1
                                    if confirm_retweet_btn:
                                        confirm_retweet_btn[0].click()
                                        time.sleep(2)
                                        self.retweet_completed = True
                                        print("Successfully retweeted post.")
                                        TwitterActionLog.objects.create(
                                            avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                            action_type='RETWEET_ACTION',
                                            action='Successfully retweeted post.',
                                            status='SUCCESS',
                                            error={'msg': ''}
                                        )
                                        # record action info
                                        self.recorder.record_action(
                                            self.owner,
                                            ActionType.RETWEET_TWEET,
                                            self.user_name,
                                            ActionResult.SUCCESSFUL,
                                            tweet=tweet_record)
                                    else:
                                        # record action info
                                        self.recorder.record_action(
                                            self.owner,
                                            ActionType.RETWEET_TWEET,
                                            self.user_name,
                                            ActionResult.FAILED,
                                            tweet=tweet_record)
                                else:
                                    self.retweet_completed = False
                                    print("Post is already retweeted.")
                                    TwitterActionLog.objects.create(
                                        avd=UserAvd.objects.get(name=self.bot.emulator_name),
                                        action_type='RETWEET_ACTION',
                                        action='Post is already retweeted.',
                                        status='SUCCESS',
                                        error={'msg': ''}
                                    )
                        except Exception as e:
                            LOGGER.exception(e)
                            tb = traceback.format_exc()
                            print("There was an error, while retweeting the post.")
                            self.retweet_completed = False
                            # record action info
                            self.recorder.record_action(
                                self.owner,
                                ActionType.RETWEET_TWEET,
                                self.user_name,
                                ActionResult.FAILED,
                                tweet=tweet_record)
                else:
                    self.retweet_completed = True

                return constant_content
        except Exception as e:
            LOGGER.exception(e)
            print(f"Something went wrong while performing action on bot {self.bot.emulator_name}")
            print(f"Error: {e}")
            raise e
        return True


class Recorder(AndroidBaseBot):

    def __init__(self, driver):
        super().__init__(driver)

    def get_action_object_from_username(self, username):
        if username in NEW_POST_EXTERNAL_USER_NAMES:
            Action = ActionForTargetAccount
            object, created = TwitterTargetAccount.objects.get_or_create(screen_name=username)
        elif username in FOLLOW_OTHER_ACCOUNTS:
            Action = ActionForOtherAccount
            object, created = TwitterOtherAccount.objects.get_or_create(screen_name=username)
        else:
            if TwitterAccount.objects.filter(screen_name=username).exists():
                Action = ActionForBotAccount
                object = TwitterAccount.objects.get(screen_name=username)
            else:
                Action = ActionForTargetAccount
                object, created = TwitterTargetAccount.objects.get_or_create(screen_name=username)

        return (Action, object)

    def record_action(self, owner, action_type, username, result, tweet=None):
        Action, object = self.get_action_object_from_username(username)
        LOGGER.info(f'Record the action "{action_type}" for user "{username}"')
        LOGGER.debug(f'Action: {Action}, object: {object}')
        LOGGER.debug(f'owner: {owner}, action_type: {action_type}, result: {result}')
        if Action is ActionForTargetAccount:
            LOGGER.debug(f'Tweet: {tweet}')
            Action.objects.create(
                owner=owner,
                action=ActionType.objects.get(id=action_type),
                result=result,
                object=object,
                tweet=tweet)
        else:
            Action.objects.create(
                owner=owner,
                action=ActionType.objects.get(id=action_type),
                result=result,
                object=object)
