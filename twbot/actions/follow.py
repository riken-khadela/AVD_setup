"""
This file contains all available follow actions.
"""
import time

from twbot.utils import *
from typing import TypeVar, Union
from main import LOGGER

T = TypeVar("T", bound=Union["WebDriver", "ActionHelpers"])


class DirectFollow:
    """
    DirectFollow: Perform follow action on given twitter username.
    Follow only if found given username else return False

    algo:
    - Start twitter app
    - Click on search button
    - Click on search bar and type target username
    - Click on first element of twitter users list.
    - Follow user if profile username match with given username else return False
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

    def input_text_in_search_bar(self):
        """
        input_text_in_search_bar: Types target username text in search bar
        """
        search_bar = self.driver().find_elements_by_xpath(
            '//android.widget.EditText[@content-desc="Search"]'
        )
        search_bar[0].send_keys(str(self.target_name))

    def click_on_people_tab(self):
        """
        click_on_people_tab: Clicks on people tab on search page.
        """
        ppl_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]'
        )
        ppl_xpath2 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]/android.widget.TextView'
        )
        ppl_btn = ppl_xpath1 or ppl_xpath2
        ppl_btn[0].click()
        # Todo: Need add wait till elements load on page

    def get_profile_elements(self):
        """
        get_profile_elements: Provides available clickable elements of target user profile.
        """
        profiles = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/screenname_item")'
        )
        for profile in profiles:
            if (
                profile.text.replace("@", "").lower()
                == self.target_name.replace("@", "").lower()
            ):
                return profile

        return False

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

    def follow_user(self, random_acc=False):
        LOGGER.debug('follow user')

        # sometimes, we need swipe tdown to let the follow button appear
        LOGGER.debug('Swipe down')
        swipe_down(self.driver)
        random_sleep()

        try:
            """
            follow_user: Clicks on follow button of target user profile page.
            """

            # get profile username
            name_holder = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
                ".widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android"
                ".widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.FrameLayout["
                "1]/android.widget.LinearLayout/android.widget.LinearLayout["
                "2]/android.widget.LinearLayout/android.widget.TextView "
            )
            name_holder1 = self.driver().find_elements_by_id(
                    'com.twitter.android:id/name')
            name_holder = name_holder or name_holder1
            profile_name = name_holder[0].text if name_holder else False
            LOGGER.debug(f'profile_name: {profile_name}')

            # get follow button path
            follow_id = self.driver().find_elements_by_id(
                "com.twitter.android:id/button_bar_follow"
            )
            if profile_name:
                follow_xpath = self.driver().find_elements_by_xpath(
                    f'//android.widget.Button[@content-desc="{profile_name}. Follow."]'
                )
            else:
                follow_xpath = []

            # click on follow button
            LOGGER.debug('click on follow button')
            follow_btn = follow_id or follow_xpath
            LOGGER.debug(f'follow_btn: {follow_btn}')
            if follow_btn:
                if follow_btn[0].text.lower() == "follow":
                    follow_btn[0].click()
                    if not random_acc:
                        print(f"Successfully followed {profile_name}.")
                        return True
            else:
                if not random_acc:
                    print(f"Already Following {profile_name}.")

            random_sleep()
            return False

        except Exception as e:
            LOGGER.exception(e)
            return False

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
        self.click_on_people_tab()
        time.sleep(5)

        profile = self.get_profile_elements()
        if profile:
            profile.click()
        else:
            return False

    @retry()
    def perform_follow(self, target_name):
        """
        perform_follow: Performs direct/username follow action.

        args:
        target_name: twitter username in lowercase without @ sign.
        """

        self.target_name = target_name
        restart_app(self.driver, 'twitter')
        self.goto_search()
        self.search_for_target()
        user_exists = self.driver().find_elements_by_id(
            "com.twitter.android:id/user_name"
        )
        if (
            user_exists
            and user_exists[0].text.replace("@", "").lower()
            == self.target_name.replace("@", "").lower()
        ):
            print("follow_user")
            self.follow_user()
            return True
        else:
            return False


class FollowActionTwo:
    """
    algo:
    - start twitter app
    - click on search button and search target user
    - click on user and get followers and follow
    - close aap

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

    def input_text_in_search_bar(self):
        """
        input_text_in_search_bar: Types target username text in search bar
        """
        search_bar = self.driver().find_elements_by_xpath(
            '//android.widget.EditText[@content-desc="Search"]'
        )
        search_bar[0].send_keys(str(self.target_name))

    def click_on_people_tab(self):
        """
        click_on_people_tab: Clicks on people tab on search page.
        """

        ppl_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]'
        )
        ppl_xpath2 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]/android.widget.TextView'
        )
        ppl_btn = ppl_xpath1 or ppl_xpath2
        ppl_btn[0].click()
        # Todo: Need add wait till elements load on page

    def get_profile_elements(self):
        """
        get_profile_elements: Provides available clickable elements of target user profile.
        """
        profiles = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/screenname_item")'
        )
        for profile in profiles:
            if (
                profile.text.replace("@", "").lower()
                == self.target_name.replace("@", "").lower()
            ):
                return profile

        return False

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

    def get_unfollow_user(self):
        """
        get_unfollow_user: Clicks on followers and get 5 unfollowed users .
        """
        names = []
        usernames = self.driver().find_elements_by_id(
            "com.twitter.android:id/screenname_item"
        )
        for user in range(len(usernames)):
            names.append(usernames[user].text.replace("@", ""))
        follow_btn_xpath = self.driver().find_elements_by_xpath(
            f'//android.widget.Button[@content-desc="Following {names[-2]}. Unfollow."]'
        )
        follow_btn_id = self.driver().find_elements_by_id(
            f"Following {names[-2]}. Unfollow."
        )
        btn = follow_btn_xpath or follow_btn_id

        if btn:
            self.swipe_up()
            time.sleep(3)
            names1 = []
            usernames = self.driver().find_elements_by_id(
                "com.twitter.android:id/screenname_item"
            )
            for user in range(len(usernames)):
                names1.append(usernames[user].text.replace("@", ""))
            return names1
        else:
            return names

    def swipe_up(self):
        """
        swipe: Swap up followers list .
        """
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
            duration=duration,
        )

    def follow_user_followers(self):
        """
        follow_user: Clicks on followers and follow 5 users .
        """
        followers = self.driver().find_elements_by_xpath(
            '//android.widget.TextView[@content-desc="followers"]'
        )
        followers[0].click()
        time.sleep(random.randrange(10, 30))
        # get username
        names = self.get_unfollow_user()
        for name in names:
            follow_btn_id = self.driver().find_elements_by_id(f"Follow {name}. Follow.")
            follow_btn_xpath = self.driver().find_elements_by_xpath(
                f'//android.widget.Button[@content-desc="Follow {name}. Follow."]'
            )
            follow_btn = follow_btn_id or follow_btn_xpath
            if follow_btn:
                follow_btn[0].click()
                time.sleep(1)
            else:
                pass

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
        self.click_on_people_tab()
        time.sleep(5)

        # open profile
        profile = self.get_profile_elements()
        if profile:
            profile.click()
        else:
            return False

    @retry()
    def perform_follow(self, target_name):
        """
        perform_follow: Performs direct/username follow action.
        """

        self.target_name = target_name
        restart_app(self.driver, 'twitter')
        self.goto_search()
        self.search_for_target()

        user_exists = self.driver().find_elements_by_id(
            "com.twitter.android:id/user_name"
        )
        if user_exists and user_exists[0].text.lower() == f"@{self.target_name}":
            print("follow_user")
            self.follow_user_followers()
            return True
        elif user_exists and user_exists[0].text == f"@{self.target_name}":
            print("follow_user")
            self.follow_user_followers()
            return True
        else:
            return False


class FollowActionThree:
    """
    algo:
    - start twitter app
    - click on search button and search target user
    - click on user and get following and follow
    - close aap

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

    def input_text_in_search_bar(self):
        """
        input_text_in_search_bar: Types target username text in search bar
        """
        search_bar = self.driver().find_elements_by_xpath(
            '//android.widget.EditText[@content-desc="Search"]'
        )
        search_bar[0].send_keys(str(self.target_name))

    def click_on_people_tab(self):
        """
        click_on_people_tab: Clicks on people tab on search page.
        """

        ppl_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]'
        )
        ppl_xpath2 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]/android.widget.TextView'
        )
        ppl_btn = ppl_xpath1 or ppl_xpath2
        ppl_btn[0].click()
        # Todo: Need add wait till elements load on page

    def get_profile_elements(self):
        """
        get_profile_elements: Provides available clickable elements of target user profile.
        """
        profiles = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/screenname_item")'
        )
        for profile in profiles:
            if (
                profile.text.replace("@", "").lower()
                == self.target_name.replace("@", "").lower()
            ):
                return profile

        return False

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
        self.click_on_people_tab()
        time.sleep(5)

        # open profile
        profile = self.get_profile_elements()
        if profile:
            profile.click()
        else:
            return False

    def get_unfollow_user(self):
        """
        get_unfollow_user: Clicks on following list and get 5 unfollowed users .
        """
        names = []
        usernames = self.driver().find_elements_by_id(
            "com.twitter.android:id/screenname_item"
        )
        for user in range(len(usernames)):
            names.append(usernames[user].text.replace("@", ""))
        follow_btn_xpath = self.driver().find_elements_by_xpath(
            f'//android.widget.Button[@content-desc="Following {names[-2]}. Unfollow."]'
        )
        follow_btn_id = self.driver().find_elements_by_id(
            f"Following {names[-2]}. Unfollow."
        )
        btn = follow_btn_xpath or follow_btn_id
        if btn:
            self.swipe_up()
            time.sleep(3)
            names1 = []
            usernames = self.driver().find_elements_by_id(
                "com.twitter.android:id/screenname_item"
            )
            for user in range(len(usernames)):
                names1.append(usernames[user].text.replace("@", ""))
            return names1
        else:
            return names

    def swipe_up(self):
        """
        swap_up: swap up following list  .
        """
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
            duration=duration,
        )

    def follow_user_following(self):
        """
        follow_user: Clicks on followers and follow 3 users .
        """
        followers = self.driver().find_elements_by_xpath(
            '//android.widget.TextView[@content-desc="following"]'
        )
        followers[0].click()
        time.sleep(random.randrange(10, 30))
        names = self.get_unfollow_user()
        for name in names:
            follow_btn_id = self.driver().find_elements_by_id(f"Follow {name}. Follow.")
            follow_btn_xpath = self.driver().find_elements_by_xpath(
                f'//android.widget.Button[@content-desc="Follow {name}. Follow."]'
            )
            follow_btn = follow_btn_id or follow_btn_xpath
            if follow_btn:
                follow_btn[0].click()
                time.sleep(1)
            else:
                pass

    @retry()
    def perform_follow(self, target_name):
        """
        perform_follow: Performs direct/username follow action.
        """

        self.target_name = target_name
        restart_app(self.driver, 'twitter')
        self.goto_search()
        self.search_for_target()
        user_exists = self.driver().find_elements_by_id(
            "com.twitter.android:id/user_name"
        )
        if user_exists and user_exists[0].text.lower() == f"@{self.target_name}":
            self.follow_user_following()
            return True
        elif user_exists and user_exists[0].text == f"@{self.target_name}":
            print("follow_user")
            self.follow_user_following()
            return True
        else:
            return False


class MultiFollow:
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

    def input_text_in_search_bar(self):
        """
        input_text_in_search_bar: Types target username text in search bar
        """
        search_bar = self.driver().find_elements_by_xpath(
            '//android.widget.EditText[@content-desc="Search"]'
        )
        search_bar[0].send_keys(str(self.target_name))

    def click_on_people_tab(self):
        """
        click_on_people_tab: Clicks on people tab on search page.
        """
        ppl_xpath1 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]'
        )
        ppl_xpath2 = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="People"]/android.widget.TextView'
        )
        ppl_btn = ppl_xpath1 or ppl_xpath2
        ppl_btn[0].click()
        # Todo: Need add wait till elements load on page

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
        self.click_on_people_tab()
        time.sleep(5)

        return True

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

    def get_first_visible_list_of_people(self):
        btns = self.driver().find_elements_by_id('com.twitter.android:id/follow_button')
        return btns

    @retry()
    def search_multi_follow_targets(self):
        restart_app(self.driver, 'twitter')
        self.goto_search()
        self.search_for_target()
