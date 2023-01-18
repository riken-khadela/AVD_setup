from selenium.webdriver.common.by import By

from main import LOGGER
from twbot.basebot import BaseBot


class Dialog(BaseBot):
    logger = LOGGER
    activity = '.DialogActivity'

    title_id = alertTitle_id = 'android:id/alertTitle'
    message_id = 'android:id/message'
    left_button_id = button2_id = 'android:id/button2'
    right_button_id = button1_id = 'android:id/button1'

    title = None

    def __init__(self, driver, logger=logger):
        super().__init__(driver)
        self.logger = logger

    def exists(self):
        if self.activity in self.get_current_activity():
            if self.title is not None:
                title = self.get_title()
                if title is not None and self.title.lower() in title.lower():
                    self.logger.debug(f'The dialog "{self.title}" exists')
                    return True
            else:
                self.logger.debug(f'The dialog exists')
                return True

    def get_title(self):
        text = self.get_text('Dialog Title', self.title_id,
                             locator_type=By.ID, timeout=0)
        self.logger.debug(f'Title: {text}')
        return text

    def get_message(self):
        text = self.get_text('Message', self.message_id,
                             locator_type=By.ID, timeout=0)
        self.logger.debug(f'Message: {text}')
        return text

    def get_left_button_text(self):
        text = self.get_text('Left button', self.left_button_id,
                             locator_type=By.ID, timeout=0)
        self.logger.debug(f'Left button text: {text}')
        return text

    def get_right_button_text(self):
        text = self.get_text('Right button', self.right_button_id,
                             locator_type=By.ID, timeout=0)
        self.logger.debug(f'Right button text: {text}')
        return text

    def click_left_button(self, element='Left button'):
        return self.click_element(element, self.left_button_id,
                                  locator_type=By.ID, timeout=0)

    def click_right_button(self, element='Left button'):
        return self.click_element(element, self.right_button_id,
                                  locator_type=By.ID, timeout=0)


class AccountBaseDiaglog(Dialog):
    title_id = 'com.twitter.android:id/alertTitle'

    def __init__(self, driver, logger=LOGGER):
        super().__init__(driver, logger=logger)
        self.logger = logger

    def click_dismiss_button(self):
        self.click_left_button()

    def click_goto_twitter_button(self):
        self.click_right_button()

    def click_learn_more_button(self):
        self.click_right_button()

    def get_title(self):
        s = super()
        text = s.get_text('Dialog Title', s.title_id,
                          locator_type=By.ID, timeout=0)
        if text:
            self.logger.debug(f'Title: {text}')
            return text

        LOGGER.debug(f'Find dialog title with title id: {self.title_id}')
        text = self.get_text('Dialog Title', self.title_id,
                             locator_type=By.ID, timeout=0)

        return text


class AccountFollowingExceededDialog(AccountBaseDiaglog):
    activity = '.dialog.FollowingExceededDialogFragmentActivity'
    title = 'Limit reached'


class AccountSuspendedDialog(AccountBaseDiaglog):
    title = 'Suspended'


class RateDialog(Dialog):
    title_id = 'de.mobileconcepts.cyberghost:id/rate_me_text'
    activity = '.view.app.AppActivity'
    title = 'Tap the stars to rate it on the Play Store.'

    def __init__(self, driver, logger=LOGGER):
        super().__init__(driver, logger=logger)
        self.logger = logger

    def click_not_now_button(self, element='Not now button'):
        self.click_left_button(element=element)

    def click_ok_button(self, element='OK button'):
        self.click_right_button(element=element)


class MaximumDevicesReachedDialog(Dialog):
    title_id = 'android:id/text1'
    activity = '.view.app.AppActivity'
    title = 'Maximum devices reached'

    def __init__(self, driver, logger=LOGGER):
        super().__init__(driver, logger=logger)
        self.logger = logger

    def click_remove_all_devices_button(self, element='Remove all devices'):
        self.click_left_button(element=element)

    def click_cancel_button(self, element='Cancel'):
        self.click_right_button(element=element)


class AuthenticationErrorDialog(Dialog):
    title_id = 'android:id/text1'
    activity = '.view.app.AppActivity'
    title = 'Authentication error'

    def __init__(self, driver, logger=LOGGER):
        super().__init__(driver, logger=logger)
        self.logger = logger

    def click_ok_button(self, element='OK'):
        self.click_right_button(element=element)


class VpnConfirmDialog(Dialog):
    app_id = package = "com.android.vpndialogs"
    activity = ".ConfirmDialog"
    name = 'Vpn Confirm Diaglog'

    def click_ok_button(self):
        self.click_right_button(element='OK button')


class NewWifiDetectedDialog(Dialog):
    title_id = 'de.mobileconcepts.cyberghost:id/tvHotspotDetected'
    title = 'Should CyberGhost encrypt and protect this connection?'
    activity = '.view.hotspot.WifiProtectionDialog'

    def __init__(self, driver, logger=LOGGER):
        super().__init__(driver, logger=logger)
        self.logger = logger

    def click_ignore_button(self, element='Ignore'):
        self.click_left_button(element=element)
