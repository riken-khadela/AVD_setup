"""
functions for storing activity log
"""

from twbot.models import TwitterActionLog


def record_action_log(user_avd, action_type, message, traceback_msg=None):
    TwitterActionLog.objects.create(avd=user_avd,
                                    action_type=action_type,
                                    action=message,
                                    error=traceback_msg)