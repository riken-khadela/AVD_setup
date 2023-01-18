import random
import time

from twbot.models import *
from twbot.actions.follow import *
from twbot.actions.like import *
from twbot.actions.comment import *
from twbot.actions.retweet import *
from twbot.actions import tweet
from twbot.utils import *
from twbot.actions.random_action import *


month_plan = {
    "week_1": {
        "likes": random.randint(25, 35),
        "retweet": random.randint(3, 7),
        "comments": random.randint(8, 12),
        "follow": random.randint(8, 12),
    },
    "week_2": {
        "likes": random.randint(35, 45),
        "retweet": random.randint(6, 10),
        "comments": random.randint(11, 15),
        "follow": random.randint(18, 22),
    },
    "week_3": {
        "likes": random.randint(45, 55),
        "retweet": random.randint(8, 12),
        "comments": random.randint(13, 17),
        "follow": random.randint(28, 32),
    },
    "week_4": {
        "likes": random.randint(55, 65),
        "retweet": random.randint(11, 15),
        "comments": random.randint(16, 20),
        "follow": random.randint(48, 52),
    },
}

hashtags = {
    "xanalia": [
        "#nft",
        "#nfts",
        "#nftcollector",
        "#nftarts",
        "#nftartist",
        "#cryptoart",
        "#cryptoartist",
    ],
    "cazicazi": ["#virtulgames", "#cryptogames", "#gamingcommunity", "#casinogame"],
}


class MixedActions(DirectFollow, FollowActionTwo, FollowActionThree, CommentActionOne, LikeActions, RetweetActionOne,
                   RandomSwipeAction, MultiFollow):

    def __init__(self, avd_id):
        self.avd = UserAvd.objects.get(id=avd_id)
        self.twitter_bot = TwitterBot(self.avd.name)
        self.driver = self.twitter_bot.driver
        self.adb = self.twitter_bot.adb
        self.target_name = '#nft'
        self.week = 'week_1'
        self.n_likes = 1
        self.n_follow = 1
        self.n_retweet = 1
        self.n_comments = 1
        super(MixedActions, self).__init__(self.driver, target_name="test_name")
        self.wait = lambda: time.sleep(random.randrange(10, 20))

    def perform_random_action(self):
        goto_home(self.driver)
        self.perform_random_swipe_action()

    def follow(self, target_name):
        self.perform_follow(target_name)

    def like(self):
        self.like_latest_post(self.target_name)

    def retweet(self):
        self.perform_retweet(self.target_name)

    def comment(self, message):
        self.perform_comment(self.target_name, message)

    def multiple_likes(self):
        if self.n_likes and self.target_name:
            self.search_post()
            for count in range(self.n_likes):
                for i in range(3):
                    res = self.like_searched_post()
                    if res:
                        break
                    else:
                        self.swipe_down()
                        time.sleep(2)
                        continue
                self.swipe_down()

    def multiple_retweet(self):
        if self.n_retweet and self.target_name:
            self.search_post_retweet()
            for count in range(self.n_retweet):
                for i in range(3):
                    res = self.retweet_searched_tweet()
                    if res:
                        break
                    else:
                        self.swipe_up()
                        time.sleep(2)
                        continue
                self.swipe_up()

    def multiple_comment(self, *messages):
        if self.n_comments and self.target_name and self.n_comments == len(messages):
            self.comment(messages[0])

            for i in range(self.n_comments - 1):
                self.comment_another_post(messages[i + 1])

    def multiple_follow(self):
        self.search_multi_follow_targets()
        follow_btn_list = self.get_first_visible_list_of_people()
        followed = 0
        # swipes = int(self.n_follow / len(follow_btn_list)) + 1
        while followed < self.n_follow:
            for count, btn in enumerate(follow_btn_list):
                btn.click()
                time.sleep(2)
                followed = followed + 1
                if count == 4:
                    break

            follow_btn_list.clear()
            n_swipes = random.randint(1, 2)
            for j in range(n_swipes):
                self.swipe_up()
            follow_btn_list = self.get_first_visible_list_of_people()

    def daily_activities(self, target_app, week, *messages):
        self.week = week
        if self.week in list(month_plan.keys()):
            self.n_likes = month_plan.get(self.week, None).get("likes", None)
            self.n_follow = month_plan.get(self.week, None).get("follow", None)
            self.n_retweet = month_plan.get(self.week, None).get("retweet", None)
            self.n_comments = month_plan.get(self.week, None).get("comments", None)
            self.target_name = random.choice(hashtags.get(target_app, None))
            self.multiple_likes()
            time.sleep(2)
            self.multiple_retweet()
            time.sleep(2)
            self.multiple_follow()
            # time.sleep(2)
            # self.multiple_comment(*messages)


