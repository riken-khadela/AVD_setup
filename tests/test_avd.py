import unittest
import os
import django
import appium
import subprocess
import random

from appium.webdriver.appium_service import AppiumService
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from PIL import Image

from log import Log
from utils import set_log, reduce_img_size
from conf import PRJ_PATH
from conf import LOG_LEVEL, LOG_DIR, LOG_IN_ONE_FILE

# setup django settings
from django.conf import settings
if not os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surviral_avd.settings')
django.setup()

from twbot.bot import TwitterBot
from twbot.utils import start_app, random_sleep
from verify import FuncaptchaAndroidUI, RecaptchaAndroidUI
from twbot.actions.profile import ProfilePage
from twbot.actions.tweet import Tweet
from utils import run_cmd, pkill_process_after_waiting
from utils import *

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
        log_dir=LOG_DIR)


class TestAvd(unittest.TestCase):

    def test_get_avd_options(self):
        #  tw = TwitterBot('android_274')
        tw = TwitterBot('android_387')
        options = tw.get_avd_options()
        LOGGER.info(f'AVD options: {options}')

    def start_appium(self, port):
        # start appium server
        LOGGER.debug(f'Start appium server, port: {port}')
        server = AppiumService()
        server.start(
            args=["--address", "127.0.0.1", "-p", str(port), "--session-override"]
        )
        if server.is_running and server.is_listening:
            LOGGER.info('Appium server is running')
            return server
        else:
            LOGGER.info('Appium server is not running')
            return False

    def stop_appium(self):
        LOGGER.debug(f'Start to kill appium')

        try:
            # Kill all running appium instances
            kill_cmd = "kill -9 $(pgrep -f appium)"
            kill_process = subprocess.Popen(
                [kill_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            # suppress ResourceWarning: unclosed file <_io.BufferedReader name=11>
            kill_process.stdout.close()
            kill_process.stderr.close()
            kill_process.wait()
        except Exception as e:
            LOGGER.exception(e)

    def start_emulator(self, name, timezone):
        LOGGER.debug(f'Start AVD: ["emulator", "-avd", "{name}"] + '
                f'["-timezone", "{timezone}"]')
        device = subprocess.Popen(
            ["emulator", "-avd", f"{name}", '-timezone', '{timezone}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        device.stdout.close()
        device.stderr.close()

        return device

    def kill_bot_process(self, appium=False, emulators=False):
        LOGGER.debug(f'Start to kill bot processes')
        LOGGER.debug(f'appium: {appium}, emulators: {emulators}')

        #  run_verbose = True
        run_verbose = False
        try:
            # Kill all running appium instances
            if appium:
                kill_cmd = "kill -9 $(pgrep -f appium)"
                run_cmd(kill_cmd, verbose=run_verbose)

                kill_cmd = "fuser -k -n tcp 4724"
                run_cmd(kill_cmd, verbose=run_verbose)

            # Kill All emulators
            if emulators:
                self.device = None
                process_names = [
                    "qemu-system-x86_64",
                    "qemu-system-x86",
                    "emulator64-crash-service",
                    "adb",
                ]
                for process in process_names:
                    kill_cmd = f"pkill --signal TERM {process}"
                    run_cmd(kill_cmd, verbose=run_verbose)
                    pkill_process_after_waiting(process, success_code=1,
                            verbose=run_verbose)

                # remove lock files to reinitiate device
                rm_cmd = f"rm {settings.AVD_DIR_PATH}/{self.emulator_name}.avd/*.lock"
                run_cmd(kill_cmd, verbose=run_verbose)

            #  time.sleep(2)

        except Exception as e:
            print("Error in killing bot instances", e)

    def get_driver(self, port=4724):
        try:
            opts = {
                "platformName": "Android",
                #  "platformVersion": "9.0",    # comment it in order to use other android version
                "automationName": "uiautomator2",
                "noSign": True,
                "noVerify": True,
                "ignoreHiddenApiPolicyError": True,
                #  "systemPort": "8212",
                # "udid": f"emulator-{self.emulator_port}",
            }

            LOGGER.debug('Start appium driver')
            LOGGER.debug(f'Driver capabilities: {opts}')

            app_driver = webdriver.Remote(
                f"http://localhost:{port}/wd/hub",
                desired_capabilities=opts,
                keep_alive=True,
            )
            self.start_driver_retires = 0
        except Exception as e:
            LOGGER.exception(e)
            raise e

        return app_driver

    def start_twitter(self, driver):
        LOGGER.info(f'Start the app: twitter')
        try:
            driver.start_activity("com.twitter.android", "com.twitter.android.StartActivity")
        except Exception as e:
            LOGGER.exception(e)
            raise e

    def test_select_birthday(self):
        avd_name = 'android_186'
        timezone = 'US/Pacific'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver()
        #  self.start_twitter(driver)

        # Scroll to select random date of birth
        birthday_field_id = driver.find_elements_by_id(
            "com.twitter.android:id/birthday_field"
        )
        if birthday_field_id:
            LOGGER.debug(f'birthday_field_id rect: {birthday_field_id[0].rect}')
        birthday_field_xpath = driver.find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[3]"
        )
        birthday_field = birthday_field_id or birthday_field_xpath
        if birthday_field:
            birthday_field[0].click()
        else:
            press_enter(driver)

        birthday_root_picker_id = 'com.twitter.android:id/date_picker'
        birthday_root_picker = driver.find_element_by_id(birthday_root_picker_id)
        LOGGER.debug(f'birthday_root_picker rect: {birthday_root_picker.rect}')

        try:
            birthday_picker_id = 'android:id/pickers'
            birthday_picker = driver.find_element_by_id(birthday_picker_id)
            #  LOGGER.debug(f'birthday_picker: {birthday_picker}')
            LOGGER.debug(f'birthday_picker rect: {birthday_picker.rect}')
            #  random_sleep()

            month_picker_relative_xpath = 'android.widget.NumberPicker[1]'
            day_picker_relative_xpath = 'android.widget.NumberPicker[2]'
            year_picker_relative_xpath = 'android.widget.NumberPicker[3]'

            middle_month_picker_relative_xpath = '//android.widget.NumberPicker[1]/android.widget.EditText'
            middle_day_picker_relative_xpath = '//android.widget.NumberPicker[2]/android.widget.EditText'
            middle_year_picker_relative_xpath = '//android.widget.NumberPicker[3]/android.widget.EditText'

            middle_month_picker = driver.find_element_by_xpath(middle_month_picker_xpath)
            middle_day_picker = driver.find_element_by_xpath(middle_day_picker_xpath)
            middle_year_picker = driver.find_element_by_xpath(middle_year_picker_xpath)

            LOGGER.debug(f'middle_month_picker rect: {middle_month_picker.rect}')
            LOGGER.debug(f'middle_day_picker rect: {middle_day_picker.rect}')
            LOGGER.debug(f'middle_year_picker rect: {middle_year_picker.rect}')

            middle_month_rect = birthday_picker.find_element_by_xpath(
                    middle_month_picker_relative_xpath).rect
            middle_day_rect = birthday_picker.find_element_by_xpath(
                    middle_day_picker_relative_xpath).rect
            middle_year_rect = birthday_picker.find_element_by_xpath(
                    middle_year_picker_relative_xpath).rect

            LOGGER.debug(f'middle_month_rect: {middle_month_rect}')
            LOGGER.debug(f'middle_day_rect: {middle_day_rect}')
            LOGGER.debug(f'middle_year_rect: {middle_year_rect}')

            # Random birth date selection with swipe
            start_x = middle_month_rect['x'] + middle_month_rect['width'] / 2
            start_y = middle_month_rect['y'] + middle_month_rect['height'] / 2
            end_x = start_x
            end_y = start_y + middle_month_rect['height']
            LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, {end_y}: {end_y}')
            LOGGER.debug('swipe month')
            for i in range(random.randint(3, 7)):
                driver.swipe(
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    duration=random.randrange(200, 250),
                )
            start_x = middle_day_rect['x'] + middle_day_rect['width'] / 2
            start_y = middle_day_rect['y'] + middle_day_rect['height'] / 2
            end_x = start_x
            end_y = start_y + middle_day_rect['height']
            LOGGER.debug('swipe day')
            for i in range(random.randint(5, 15)):
                driver.swipe(
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    duration=random.randrange(100, 150),
                )
            start_x = middle_year_rect['x'] + middle_year_rect['width'] / 2
            start_y = middle_year_rect['y'] + middle_year_rect['height'] / 2
            end_x = start_x
            end_y = start_y + middle_year_rect['height']
            LOGGER.debug('swipe year')
            for i in range(random.randint(17, 19)):
                driver.swipe(
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    duration=random.randrange(200, 550),
                )
        except Exception as e:
            LOGGER.exception(e)
            raise e

    def test_click_button_create_account(self):
        avd_name = 'android_233'
        timezone = 'US/Pacific'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver()
        self.driver = lambda x=1: driver
        #  self.start_twitter(driver)

        # Find and click on Create Account button
        create_account_btn_id_1 = self.driver().find_elements_by_id(
            "com.twitter.android:id/ocf_button"
        )
        if create_account_btn_id_1:
            LOGGER.debug(f'create_account_btn: {create_account_btn_id_1}')
            create_account_btn_id_1[1].click()
        else:

            create_account_btn_id = self.driver().find_elements_by_id(
                "com.twitter.android:id/primary_action"
            )
            create_account_btn_res_id = self.driver().find_elements_by_android_uiautomator(
                'new UiSelector().resourceId("com.twitter.android:id/cta_button")'
            )
            create_account_btn_xpath = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
                ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout["
                "2]/android.widget.LinearLayout/android.widget.Button"
            )
            create_account_btn = (
                    create_account_btn_id
                    or create_account_btn_res_id
                    or create_account_btn_xpath
            )
            LOGGER.debug(f'create_account_btn: {create_account_btn}')
            create_account_btn[0].click()

    def test_phone_registered(self):
        avd_name = 'android_7'
        timezone = 'US/Pacific'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver()
        self.driver = lambda x=1: driver
        #  self.start_twitter(driver)

        # Find phone number field and fill with united state number
        phone_field_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/phone_or_email_field"
        )
        phone_field_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[2]"
        )
        phone_field = phone_field_id or phone_field_xpath

        text = phone_field[0].text
        LOGGER.info(f'text: {text}')

        #  style = phone_field[0].value_of_css_property('style')
        #  LOGGER.info(f'style: {style}')

    def test_recaptcha(self):
        #  avd_name = 'android_199'
        #  timezone = 'US/Pacific'
        avd_name = 'android_208'
        timezone = 'US/Central'
        port = 4724

        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)
        #  self.driver = lambda x=1: driver
        #  self.start_twitter(driver)

        #  random_sleep()
        #  captcha_checkbox_xpath = '//android.widget.CheckBox[@resource-id="recaptcha-anchor"]'
        #  captcha_checkbox = driver.find_element_by_xpath(captcha_checkbox_xpath)
        #  captcha_checkbox.click()
        #
        #  random_sleep(10, 20)

        # info: Cannot contact reCAPTCHA. Check your connection and try again.
        captcha_no_contact_info_id = 'android:id/message'
        captcha_no_contact_button_id = 'android:id/button1'

        captcha_form_xpath = '//android.view.View[@resource-id="rc-imageselect"]'
        captcha_form_xpath1 = ('//android.widget.FrameLayout/android.widget.LinearLayout/'
                'android.widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/'
                'android.view.View[3]/android.view.View[2]')

        captcha_form = driver.find_elements_by_xpath(captcha_form_xpath)
        captcha_form1 = driver.find_elements_by_xpath(captcha_form_xpath1)

        captcha_form = captcha_form or captcha_form1
        captcha_form = captcha_form[0]

        LOGGER.debug(f'reCAPTCHA form location: {captcha_form.location}')
        LOGGER.debug(f'reCAPTCHA form size: {captcha_form.size}')
        LOGGER.debug(f'reCAPTCHA window size: {driver.get_window_size()}')
        

        img_file = PRJ_PATH / 'captcha.png'
        captcha_form.screenshot(str(img_file.absolute()))

        small_img_file = PRJ_PATH / 'captcha_small.png'

        reduce_factor = 3
        
        captcha = Funcaptcha(driver)
        captcha.solve_captcha(img_file, reduce_factor=reduce_factor,
                captcha_form_xpath=captcha_form_xpath)

        #  if img_file.exists():
        #      #  img = Image.open(img_file)
        #      #  LOGGER.info(f'Original size: {img.size}')
        #      #
        #      #  width = img.size[0] // reduce_factor
        #      #  height = img.size[1] // reduce_factor
        #      #
        #      #  small_img = img.resize((width, height), Image.ANTIALIAS)
        #      #  small_img.save(small_img_file, optimize=True, quality=80)
        #
        #      small_img_file = reduce_img_size(img_file, reduce_factor=reduce_factor)
        #
        #      #  random_sleep()
        #
        #      captcha_resolver = self.get_captcha(small_img_file)
        #
        #      if captcha_resolver:
        #          form_x = captcha_form.location['x']
        #          form_y = captcha_form.location['y']
        #
        #          for x, y in eval(captcha_resolver):
        #              real_x = x * reduce_factor + form_x
        #              real_y = y * reduce_factor + form_y
        #              LOGGER.debug(f'real_x: {real_x}, real_y: {real_y}')
        #
        #              action = TouchAction(driver)
        #
        #              #  action.long_press(x=real_x, y=real_y).perform()
        #              action.tap(x=real_x, y=real_y).perform()
        #              #  driver.tap([(real_x, real_y)], duration=500)
        #              #  random_sleep()


    def get_captcha(self, img_file):
        from dbc_api_python3 import deathbycaptcha

        # Put your DBC account username and password here.
        username = "noborderz"
        password = r"/+eQm@>;Q:Td8?MA"
        # you can use authtoken instead of user/password combination
        # activate and get the authtoken from DBC users panel
        authtoken = ""
        captcha_file = 'test_traffic_light.png'  # image
        #  captcha_file = 'test_bus.png'  # image
        #  captcha_file = 'test_vehicles.png'  # image
        captcha_file = './captcha_small.png'  # image
        captcha_file = str(img_file.absolute())

        #  client = deathbycaptcha.SocketClient(username, password)
        #to use http client
        client = deathbycaptcha.HttpClient(username, password)

        retry_times = 3
        times = 0

        while times < retry_times:
            try:
                balance = client.get_balance()
                LOGGER.info(f'balance: {balance}')

                # Put your CAPTCHA file name or file-like object, and optional
                # solving timeout (in seconds) here:
                captcha = client.decode(captcha_file, type=2, timeout=30)
                if captcha:
                    # The CAPTCHA was solved; captcha["captcha"] item holds its
                    # numeric ID, and captcha["text"] item its list of "coordinates".
                    LOGGER.debug("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))

                    if not captcha['text']:  # check if the CAPTCHA was incorrectly solved
                        client.report(captcha["captcha"])
                    else:
                        return captcha['text']
                else:
                    times += 1
                    LOGGER.debug(f'Found no captcha, then retry: {times}')
                    continue
            except deathbycaptcha.AccessDeniedException:
                # Access to DBC API denied, check your credentials and/or balance
                times += 1
                LOGGER.debug(f'AccessDeniedException, then retry: {times}')
                LOGGER.info("error: Access to DBC API denied, check your credentials and/or balance")
                continue
            except Exception as e:
                LOGGER.exception(e)
                times += 1
                LOGGER.debug(f'Other exception, then retry: {times}')

        return None

    def test_funcaptcha(self):
        avd_name = 'android_366'
        avd_name = 'android_159'
        timezone = 'US/Hawaii'
        port = 4724

        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        resolver = FuncaptchaAndroidUI(driver)
        resolver.resolve_all_with_coordinates_api()

    def test_recaptcha_1(self):
        avd_name = 'android_482'
        timezone = 'US/Aleutian'
        port = 4724

        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        captcha = RecaptchaAndroidUI(driver)
        captcha.resolve_all_with_coordinates_api()

    def test_recaptcha_save_effect_image(self):
        avd_name = 'android_482'
        timezone = 'US/Aleutian'
        port = 4724

        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        captcha = RecaptchaAndroidUI(driver)
        #  random_sleep(5, 10)
        captcha.save_captcha_effect_img()

    def test_get_display_area(self):
        avd_name = 'android_482'
        timezone = 'US/Aleutian'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        profile = ProfilePage(driver)

        profile.get_list_max_display_area()
        profile.get_activity()

    def test_profile_exists(self):
        avd_name = 'android_482'
        timezone = 'US/Aleutian'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        profile = ProfilePage(driver)

        timeout = 0
        #  result = profile.exists(timeout=timeout)
        #  LOGGER.info(f'result: {result}')
        profile.get_activity()

    def test_swipe_to_top(self):
        avd_name = 'android_482'
        timezone = 'US/Aleutian'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        profile = ProfilePage(driver)

        items = profile.get_item_list()
        LOGGER.info(f'len(items): {len(items)}')
        #  profile.swipe_item_top_to_top(items[0])
        #  profile.swipe_item_bottom_to_top(items[0])
        LOGGER.debug(f'item2 rect: {items[1].rect}')

    def test_check_pinned_tweet(self):
        avd_name = 'android_482'
        timezone = 'US/Aleutian'
        port = 4724

        #  self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        profile = ProfilePage(driver)
        t = Tweet(driver)

        items = profile.get_item_list()
        LOGGER.info(f'len(items): {len(items)}')
        pinned_tweet = items[0]

        tweet_element = profile.driver.find_element_by_id(
                t.tweet_element_id)
        content = tweet_element.get_attribute('content-desc')
        LOGGER.debug(f'tweet_element: {tweet_element}')
        LOGGER.debug(f'content: {content}')
        ele = tweet_element.find_element_by_id(
                t.tweet_element_id)
        LOGGER.debug(f'ele: {ele}')
        content = ele.get_attribute('content-desc')
        LOGGER.debug(f'content: {content}')

    def test_item_list(self):
        avd_name = 'android_83'
        timezone = 'US/Mountain'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)

        items = p.get_item_list()
        for i in items:
            #  LOGGER.info(f'item {i}: {i.tag_name}')
            LOGGER.debug(i.get_attribute('class'))

    def test_item_list(self):
        avd_name = 'android_83'
        timezone = 'US/Mountain'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)

        items = p.get_tweet_list()
        for i in items:
            #  LOGGER.info(f'item {i}: {i.tag_name}')
            LOGGER.debug(i.get_attribute('class'))

    def test_swipe_profile_header(self):
        avd_name = 'android_83'
        timezone = 'US/Mountain'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)
        p.swipe_profile_header()

    def test_get_latest_tweet(self):
        avd_name = 'android_83'
        timezone = 'US/Mountain'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)
        p.get_latest_tweet()

    def test_tweet_child(self):
        avd_name = 'android_455'
        timezone = 'US/Mountain'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)

        items = p.get_item_list()
        item1 = items[0]
        for i in items:
            #  LOGGER.info(f'item {i}: {i.tag_name}')
            LOGGER.debug(i.get_attribute('class'))

        result = p.tweet.is_tweet_display(item1)
        LOGGER.info(f'result: {result}')

    def test_tweet_display(self):
        avd_name = 'android_455'
        timezone = 'US/Mountain'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)

        items = p.get_item_list()
        item1 = items[0]
        for i in items:
            #  LOGGER.info(f'item {i}: {i.tag_name}')
            LOGGER.debug(i.get_attribute('class'))

        result = p.is_item_display(item1)
        LOGGER.info(f'result: {result}')

    def test_get_activity(self):
        avd_name = 'android_483'
        timezone = 'US/Hawaii'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        self.start_emulator(avd_name, timezone)
        driver = self.get_driver(port=port)

        p = ProfilePage(driver)

        result = p.get_activity()
        LOGGER.info(f'result: {result}')

    def test_vpn(self):
        avd_name = 'android_483'
        timezone = 'US/Hawaii'
        port = 4724

        #  self.kill_bot_process(appium=True, emulators=True)
        self.stop_appium()
        self.start_appium(port=port)
        #  self.start_emulator(avd_name, timezone)
        #  driver = self.get_driver(port=port)

        tb = TwitterBot(avd_name)
        result = tb.connect_to_vpn()
        LOGGER.info(f'result: {result}')
