from django.contrib import admin
from rangefilter.filter import DateTimeRangeFilter

from twbot.models import *

# Register your models here.

#  admin.site.register(TwitterAccount)
admin.site.register(TwitterUser)
admin.site.register(TwitterJob)
#  admin.site.register(TwitterActionLog)
#  admin.site.register(Tweet)
#  admin.site.register(UserAvd)
admin.site.register(UrlEngageTask)
admin.site.register(EngageTask)
#  admin.site.register(TwitterOtherAccount)


class UserAvdAdmin(admin.ModelAdmin):
    list_display = ('name', 'port', 'twitter_account', "account_status", 'timezone', 'country',
                    'created', 'updated')
    list_filter = ["twitter_account", "twitter_account__status"]
    search_fields = ["twitter_account__full_name", "name"]

    @admin.display(ordering='twitter_account__status')
    def account_status(self, obj):
        try:
            return obj.twitter_account.status
        except:
            return "-"


admin.site.register(UserAvd, UserAvdAdmin)


class TwitterAccountAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'screen_name', 'phone', 'password', 'status'
                    , 'created', 'updated', 'profile_updated')
    list_filter = [("created", DateTimeRangeFilter), ("updated", DateTimeRangeFilter), "status", "profile_updated"]
    search_fields = ["full_name", "phone"]


admin.site.register(TwitterAccount, TwitterAccountAdmin)


class TwitterActionLogAdmin(admin.ModelAdmin):
    list_display = ('avd', 'action_type', 'status', 'action')


admin.site.register(TwitterActionLog, TwitterActionLogAdmin)


class ActionTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'remark', 'created', 'updated')


admin.site.register(ActionType, ActionTypeAdmin)


class ActionForBotAccountAdmin(admin.ModelAdmin):
    list_display = ('owner', 'action', 'object', 'result', 'created')


admin.site.register(ActionForBotAccount, ActionForBotAccountAdmin)


class ActionForTargetAccountAdmin(admin.ModelAdmin):
    list_display = ('owner', 'action', 'object', 'result', 'tweet', 'created')


admin.site.register(ActionForTargetAccount, ActionForTargetAccountAdmin)


class ActionForOtherAccountAdmin(admin.ModelAdmin):
    list_display = ('owner', 'action', 'object', 'result', 'created')

admin.site.register(ActionForOtherAccount, ActionForOtherAccountAdmin)

class TweetAdmin(admin.ModelAdmin):
    list_display = ('text', 'created')

admin.site.register(Tweet, TweetAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('tweet', 'comment', 'is_used', 'created')

admin.site.register(Comment, CommentAdmin)

class TwitterOtherAccountAdmin(admin.ModelAdmin):
    #  list_display = ('full_name', 'status', 'screen_name', 'created')
    list_display = ('screen_name', 'status', 'created')

admin.site.register(TwitterOtherAccount, TwitterOtherAccountAdmin)

class TwitterTargetAccountAdmin(admin.ModelAdmin):
    #  list_display = ('full_name', 'status', 'screen_name', 'created')
    list_display = ('screen_name', 'status', 'created')

admin.site.register(TwitterTargetAccount, TwitterTargetAccountAdmin)

class TweetForTargetAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'text', 'publish_time', 'is_retweeted',
            'status', 'created')

admin.site.register(TweetForTargetAccount, TweetForTargetAccountAdmin)

class PhoneAdmin(admin.ModelAdmin):
    list_display = ('number', 'pid', 'user', 'is_banned', 'ban_result',
            'created')

admin.site.register(Phone, PhoneAdmin)

class SmsAdmin(admin.ModelAdmin):
    list_display = ('number', 'content', 'purpose', 'created')

admin.site.register(Sms, SmsAdmin)
