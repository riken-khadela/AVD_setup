"""Exceptions for twitter bot"""


class PhoneRegisteredException(Exception):
    """This phone number is already registered to an account."""


class CannotGetSms(Exception):
    pass


class CannotRegisterThisPhoneNumberException(Exception):
    """We can't currently register this phone number"""


class AccountSuspendedException(Exception):
    pass


class AccountLimitedException(Exception):
    pass


class CannotStartDriverException(Exception):
    pass


class GetSmsCodeNotEnoughBalance(Exception):
    """Not Enough Balance"""
