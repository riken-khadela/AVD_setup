"""
This file consist all available like actions.
"""
import time

from twbot.utils import *
from twbot.models import *
from twbot.engagement.bot import TwitterBot


class LikeActions:
    """
    Algo:
    - Launch twitter app
    - Go to search page
    - Search for target username and open profile
    - Perform like action on the latest post
    """

    def __init__(self, driver, target_name):
        self.driver = driver
        self.target_name = target_name

    def get_tweets(self):
        for i in range(3):
            tweets = self.driver().find_elements_by_id('com.twitter.android:id/outer_layout_row_view_tweet')
            if tweets:
                break
            else:
                swipe_up(self.driver)
                time.sleep(2)
        return tweets

    def open_pinned_post(self, tweets):
        for tweet in tweets:
            # Get content description of the tweet
            try:
                content_desc = tweet.find_elements_by_class_name('android.view.ViewGroup')[-1].get_attribute('content-desc')

                if 'Pinned Tweet' in content_desc:
                    # Get different post information
                    id_name = content_desc.split(".")[0].split(" ")[0]
                    screen_name = content_desc.split(".")[0].split(" ")[1]
                    element_xy_bounds = tweet.get_attribute('bounds')
                    element_coordinates = element_xy_bounds.replace("'", " ").replace("][", ",").replace("[", " ").replace(
                        "]", " ").replace(" ", "").split(",")
                    x1 = int(element_coordinates[0])
                    y1 = int(element_coordinates[1])
                    x2 = int(element_coordinates[2])
                    y2 = int(element_coordinates[3])

                    # Open tweet
                    self.driver().tap([(x1, y1)])
                    time.sleep(5)
                    return True
            except:
                return False        

        return False

    def open_retweeted_post(self, tweets):
        for tweet in tweets:
            # Get content description of the tweet
            try:
                content_desc = tweet.find_elements_by_class_name('android.view.ViewGroup')[-1].get_attribute('content-desc')

                if 'Retweeted' in content_desc:
                    # Get different post information
                    id_name = content_desc.split(".")[0].split(" ")[0]
                    screen_name = content_desc.split(".")[0].split(" ")[1]
                    element_xy_bounds = tweet.get_attribute('bounds')
                    element_coordinates = element_xy_bounds.replace("'", " ").replace("][", ",").replace("[", " ").replace(
                        "]", " ").replace(" ", "").split(",")
                    x1 = int(element_coordinates[0])
                    y1 = int(element_coordinates[1])
                    x2 = int(element_coordinates[2])
                    y2 = int(element_coordinates[3])

                    # Open tweet
                    self.driver().tap([(x1, y1)])
                    time.sleep(5)
                    return True
            except:
                return False

        return False

    def open_generic_post(self, tweets):
        for tweet in tweets:
            # Get content description of the tweet
            try:
                content_desc = tweet.find_elements_by_class_name('android.view.ViewGroup')[-1].get_attribute('content-desc')

                if 'Pinned Tweet' in content_desc or "Retweeted" in content_desc or "Promoted" in content_desc:
                    pass
                else:
                    # Get different post information
                    id_name = content_desc.split(".")[0].split(" ")[0]
                    screen_name = content_desc.split(".")[0].split(" ")[1]
                    element_xy_bounds = tweet.get_attribute('bounds')
                    element_coordinates = element_xy_bounds.replace("'", " ").replace("][", ",").replace("[", " ").replace(
                        "]", " ").replace(" ", "").split(",")
                    x1 = int(element_coordinates[0])
                    y1 = int(element_coordinates[1])
                    x2 = int(element_coordinates[2])
                    y2 = int(element_coordinates[3])

                    # Open tweet
                    self.driver().tap([(x1, y1)])
                    time.sleep(5)
                    return True
            except:
                return False

        return False

    def open_latest_post(self, is_pinned=False, is_retweeted=False):
        """
        ALGO TO FIND LATEST POST(DEPENDING ON PARAMETER):
        - get list of posts on the page
        - get content-desc
        - identify post type according to the input
        - open post
        """
        for i in range(10):
            for i in range(3):
                tweets = self.get_tweets()
                if tweets:
                    break
                else:
                    swipe_up(self.driver)

                tweets = None
                print("Couldn't get tweets.")

            if is_pinned:
                open_resp = self.open_pinned_post(tweets)

            elif is_retweeted:
                open_resp = self.open_retweeted_post(tweets)

            else:
                open_resp = self.open_generic_post(tweets)

            if not open_resp:
                swipe_up(self.driver)
                time.sleep(2)
            else:
                break

        if open_resp:
            return True
        else:
            return False

    def like_opened_post(self):
        LOGGER.debug('Like opened post')
        for i in range(5):
            time.sleep(2)

            # check if already liked
            already_liked_btn_accs_id = self.driver().find_elements_by_accessibility_id('Like (Liked)')
            already_liked_btn_xpath = self.driver().find_elements_by_xpath(
                '//android.widget.ImageButton[@content-desc="Like (Liked)"]')
            already_liked = already_liked_btn_xpath or already_liked_btn_accs_id
            if already_liked:
                return "Post is already Liked."

            # find like button
            like_btn_accs_id = self.driver().find_elements_by_accessibility_id('Like')
            like_btn_xpath = self.driver().find_elements_by_xpath('//android.widget.ImageButton[@content-desc="Like"]')
            like_btn = like_btn_accs_id or like_btn_xpath

            if like_btn:
                like_btn[0].click()
                return f"Successfully liked {self.target_name}'s latest post."
            else:
                swipe_up(self.driver)

        return False

    @retry()
    def like_latest_post(self, is_pinned=False, is_retweeted=False):
        restart_app(self.driver, 'twitter')
        time.sleep(2)

        # Search for target username and open profile
        goto_search(self.driver)
        time.sleep(2)
        search_for_target(self.driver, target=self.target_name)
        time.sleep(5)

        # Open latest post
        open_resp = self.open_latest_post(is_pinned, is_retweeted)
        assert open_resp, "Couldn't find a tweet other than pinned or retweeted in 6 tries."

        # Like Opened Post
        like_resp = self.like_opened_post()
        assert like_resp, "Couldn't Find Like button in 5 swipes."

        return like_resp

    def search_for_target_multiple_actions(self, driver, target):
        # click on search bar
        ele_one = self.driver().find_elements_by_xpath(
            '//android.widget.RelativeLayout[@content-desc="Search Twitter"]')
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
    def search_post(self):
        restart_app(self.driver, 'twitter')
        time.sleep(2)

        # Search for target username and open profile
        goto_search(self.driver)
        time.sleep(2)
        self.search_for_target_multiple_actions(self.driver, target=self.target_name)
        time.sleep(5)
        return True

    def get_likes_count(self):
        likes = []
        like_elements = self.driver().find_elements_by_id('com.twitter.android:id/inline_like')
        time.sleep(2)
        for element in like_elements:
            children = element.find_elements_by_class_name('android.widget.FrameLayout')
            if children:
                text_view_pre = children[1].find_elements_by_class_name('android.widget.TextView')
                if ',' in str(text_view_pre[0].text):
                    like_text = ''.join(str(text_view_pre[0].text).split(','))
                    likes.append(int(like_text))
                elif 'K' in str(text_view_pre[0].text):
                    like_text = str(text_view_pre[0].text).split(',')[0]
                    if '.' in like_text:
                        likes.append(float(like_text)*1000)
                    else:
                        likes.append(int(like_text)*1000)
                else:
                    likes.append(int(text_view_pre[0].text))
        return likes

    @retry()
    def like_searched_post(self):
        try:
            likes_pre = self.get_likes_count()
            like_elements = self.driver().find_elements_by_id('com.twitter.android:id/inline_like')
            time.sleep(2)
            count = 0
            for element in like_elements:
                count = count + 1
                element.click()
                time.sleep(2)

            # likes_post = self.get_likes_count()
            # for index, tup in enumerate(zip(likes_pre, likes_post)):
            #     if tup[0] < tup[1]:
            #         like_elements[index].click()
            #         time.sleep(2)
            #         count = count - 1

            return count
        except Exception as e:
            print(e)
            return False

    def like_posts(self, limit):
        liked = 0
        retries = 0
        for i in range(limit + 5):
            if retries > 3:
                return False

            if liked >= limit:
                return f"Successfully liked {limit} post(s) on {self.target_name}"

    """
    Open a post if it hasn't reached required likes limit
    """
    def open_conditional_post(self, total_posts, total_likes):
        LOGGER.debug(f'total_likes: {total_likes}, total_posts: {total_posts}')
        if total_posts != 0:
            required_likes = int(round(int(total_likes) / int(total_posts)))
        else:
            required_likes = int(total_likes)

        for i in range(6):
            tweets = self.driver().find_elements_by_id('com.twitter.android:id/outer_layout_row_view_tweet')

            if not tweets:
                tweets = []

            for tweet in tweets:
                likes_on_post = "None"

                like_items_xpath = tweet.find_elements_by_id('com.twitter.android:id/inline_like')
                if like_items_xpath:
                    likes_on_post = like_items_xpath[0].find_elements_by_xpath('//*')[-1].text.replace(",", "")

                    if likes_on_post == '':
                        likes_on_post = "0"

                    # convert to full from if abbreviated
                    likes_on_post = string_to_int(likes_on_post)
                    
                if likes_on_post == "None":
                    continue

                if likes_on_post < required_likes:
                    try:
                        content_desc = tweet.find_elements_by_class_name('android.view.ViewGroup')[-1].get_attribute('content-desc')

                        if 'Pinned Tweet' in content_desc or "Retweeted" in content_desc or "Promoted" in content_desc:
                            pass
                        else:
                            # Get different post information
                            id_name = content_desc.split(".")[0].split(" ")[0]
                            screen_name = content_desc.split(".")[0].split(" ")[1]
                            element_xy_bounds = tweet.get_attribute('bounds')
                            element_coordinates = element_xy_bounds.replace("'", " ").replace("][", ",").replace("[", " ").replace(
                                "]", " ").replace(" ", "").split(",")
                            x1 = int(element_coordinates[0])
                            y1 = int(element_coordinates[1])
                            x2 = int(element_coordinates[2])
                            y2 = int(element_coordinates[3])

                            # Open tweet
                            self.driver().tap([(x1, y1)])
                            time.sleep(5)
                            return True
                    except Exception as e:
                        return False

            swipe_up(self.driver)

        return False
