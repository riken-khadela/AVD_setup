import difflib
import json
import random
import re
import time
import traceback

from selenium.webdriver.support.wait import WebDriverWait

from constants import COUNTRY_CODES
from twbot.utils import *
from twbot.models import *
from appium import webdriver
from selenium.common.exceptions import *
from surviral_avd.settings import BASE_DIR
from ppadb.client import Client as AdbClient
from django.conf import settings
from twbot.actions.voice_recaptcha_solver import *
from selenium.common.exceptions import WebDriverException
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from twbot.actions.voice_recaptcha_solver import (
    audio_to_text,
    load_audio,
    start_recording,
    stop_recording,
)

from conf import TWITTER_VERSIONS


class TwitterBot:
    def __init__(self, emulator_name, start_appium=True, start_adb=True):
        self.emulator_name = emulator_name
        self.user_avd = UserAvd.objects.get(name=emulator_name)
        self.kill_bot_process(appium=True, emulators=True)
        self.app_driver = None
        self.emulator_port = None
        self.service = self.start_appium(port=4724) if start_appium else None
        self.adb = AdbClient() if start_adb else None
        self.device = None
        self.phone = (
            self.user_avd.twitter_account.phone
            if self.user_avd.twitter_account
            else None
        )
        self.get_device_retires = 0
        self.start_driver_retires = 0
        log_activity(
            self.user_avd.id,
            action_type="TwitterBotInit",
            msg=f"Initiated TwitterBot instance with {self.user_avd.name}",
            error=None,
        )

    def start_appium(self, port):
        # start appium server
        server = AppiumService()
        server.start(
            args=["--address", "127.0.0.1", "-p", str(port), "--session-override"]
        )
        if server.is_running and server.is_listening:
            log_activity(
                self.user_avd.id,
                action_type="StartAppiumServer",
                msg=f"Started Appium server for {self.user_avd.name}",
                error=None,
            )
            return server
        else:
            log_activity(
                self.user_avd.id,
                action_type="StartAppiumServer",
                msg=f"Failed to start Appium server for {self.user_avd.name}",
                error=f"server status is not running and listening.",
            )
            return False

    def get_device(self):
        name = self.emulator_name

        if not self.device:
            self.device = subprocess.Popen(
                ["emulator", "-avd", f"{name}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            time.sleep(5)
            log_activity(
                self.user_avd.id,
                action_type="StartAvd",
                msg=f"Started AVD for {self.user_avd.name}",
                error=None,
            )

        if self.get_adb_device():
            self.get_device_retires = 0
            # self.get_adb_device().wait_boot_complete(timeout=100)
        else:
            self.device = False
            if self.get_device_retires >= 3:
                log_activity(
                    self.user_avd.id,
                    action_type="StartAvd",
                    msg=f"Failed to start AVD for {self.user_avd.name}",
                    error="Couldn't get device",
                )
                raise Exception("Couldn't get device.")

            self.get_device_retires += 1

            # kill all running devices/emulators
            print("killed in get_device")
            self.kill_bot_process(emulators=True)
            time.sleep(2)
            self.get_device()

        return self.device

    def check_apk_installation(self):
        if not self.driver().is_app_installed("com.twitter.android"):
            self.install_apk(self.emulator_port, "twitter")
            log_activity(
                self.user_avd.id,
                action_type="InstallTwitter",
                msg=f"Twitter app installed successfully.",
                error=None,
            )
        # if not self.driver().is_app_installed("com.surfshark.vpnclient.android"):
        #     self.install_apk(self.emulator_port, "surfshark")
        if not self.driver().is_app_installed("com.instagram.android"):
            self.install_apk(self.emulator_port, "instagram")
            log_activity(
                self.user_avd.id,
                action_type="InstallInstagram",
                msg=f"Instagram app installed successfully.",
                error=None,
            )
        # if not self.driver().is_app_installed("com.github.shadowsocks"):
        #     self.install_apk(self.emulator_port, "shadowsocks")
        #     log_activity(
        #         self.user_avd.id,
        #         action_type="InstallInstagram",
        #         msg=f"Instagram app installed successfully.",
        #         error=None,
        #     )
        if not self.driver().is_app_installed("com.nordvpn.android"):
            self.install_apk(self.emulator_port, "nord_vpn")
            log_activity(
                self.user_avd.id,
                action_type="NordVPN",
                msg=f"NordVPN app installed successfully.",
                error=None,
            )

    def get_adb_device(self):
        for x in range(20):
            if self.adb.devices():
                try:
                    response = self.adb.devices()[0].shell("getprop sys.boot_completed | tr -d '\r'")
                    if "1" in response:
                        self.emulator_port = self.adb.devices()[0].serial.split("-")[-1]
                        return self.adb.devices()[0]
                except Exception as e:
                    print(e)
            time.sleep(x)

    def start_driver(self):
        try:
            opts = {
                "platformName": "Android",
                "platformVersion": "9.0",
                "automationName": "uiautomator2",
                "noSign": True,
                "noVerify": True,
                "ignoreHiddenApiPolicyError": True,
                "systemPort": "8210",
                # "udid": f"emulator-{self.emulator_port}",
            }

            self.app_driver = webdriver.Remote(
                "http://localhost:4724/wd/hub",
                desired_capabilities=opts,
                keep_alive=True,
            )
            self.start_driver_retires = 0
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Driver started successfully",
                error=None,
            )
        except Exception as e:
            print(f"Error: {e}")
            tb = traceback.format_exc()
            if self.start_driver_retires > 5:
                print("================ Couldn't start driverCouldn't start driver")
                log_activity(
                    self.user_avd.id,
                    action_type="ConnectAppium",
                    msg=f"Error while connecting with appium server",
                    error=tb,
                )
                raise Exception("Couldn't start driver")

            self.start_driver_retires += 1
            print(f"appium server starting retries: {self.start_driver_retires}")
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Error while connecting with appium server",
                error=f"Failed to connect with appium server retries_value: {self.start_driver_retires}",
            )
            self.driver()

    def driver(self, check_verification=True):
        assert self.get_device(), "Device Didn't launch."

        try:
            session = self.app_driver.session
        except Exception as e:
            tb = traceback.format_exc()
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Connect with Appium server",
                error=tb,
            )
            self.start_driver()

        # check and bypass google captcha
        self.perform_verification()
        popup = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Wait")'
        )
        popup[0].click() if popup else None
        return self.app_driver

    def create_avd(self, avd_name, package=None, device=None):
        default_package = "system-images;android-28;default;x86"

        try:
            if not package:
                cmd = f'avdmanager create avd --name {avd_name} --package "{default_package}"'
            else:
                cmd = f'avdmanager create avd --name {avd_name} --package "{package}"'

            if device:
                cmd += f" --device {device}"

            p = subprocess.Popen(
                [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
            )
            time.sleep(1)
            p.communicate(input=b"\n")
            p.wait()
            return True

        except Exception as e:
            print(e)
            return False

    def install_apk(self, port, app_name):
        try:
            if app_name.lower() == "instagram":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/instagram.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallInstagramApk",
                    msg=f"Installation of instagram apk",
                    error=None,
                )
            elif app_name.lower() == "twitter":
                #  cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/twitter.apk')}"
                twitter_version = random.choice(TWITTER_VERSIONS)
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, f'apk/twitter_{twitter_version}.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallTwitterApk",
                    msg=f"Installation of twitter apk",
                    error=None,
                )
            # elif app_name.lower() == "shadowsocks":
            #     cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/shadowsocks.apk')}"
            #     log_activity(
            #         self.user_avd.id,
            #         action_type="InstallShadowsockApk",
            #         msg=f"Installation of shadowsocks apk",
            #         error=None,
            #     )
            elif app_name.lower() == "nord_vpn":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/nord_vpn.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallNordVPNApk",
                    msg=f"Installation of NordVPN apk",
                    error=None,
                )
            else:
                return False
            p = subprocess.Popen(
                [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
            )
            p.wait()
            return True
        except Exception as e:
            print(e)
            return False

    def run_script(self, *args, **options):
        self.perform_login()
        print("login process completed")
        self.service.stop()
        print("stopped appium server")
        self.device.terminate()
        print("terminated emulator")

    def set_proxy(self, proxy, port):
        try:
            # remove already set proxy settings
            rm_cmd1 = f"adb -s emulator-{port} shell settings delete global http_proxy"
            rm_cmd2 = f"adb -s emulator-{port} shell settings delete global global_http_proxy_port"
            rm_cmd3 = f"adb -s emulator-{port} shell settings delete global global_http_proxy_host"
            rm_exec = subprocess.Popen(
                [rm_cmd1, rm_cmd2, rm_cmd3], stdin=subprocess.PIPE, shell=True
            )

            # set new proxy
            set_cmd = (
                f"adb -s emulator-{port} shell settings put global http_proxy {proxy}"
            )
            set_exec = subprocess.Popen([set_cmd], stdin=subprocess.PIPE, shell=True)
            log_activity(
                self.user_avd.id,
                action_type="SetProxy",
                msg=f"Setup a proxy in avd",
                error=None,
            )
            return True
        except:
            log_activity(
                self.user_avd.id,
                action_type="SetProxyFailed",
                msg=f"Failed to setup a proxy in avd",
                error=traceback.format_exc(),
            )
            return False

    def kill_process(self, port):
        try:
            cmd = f"lsof -t -i tcp:{port} | xargs kill -9"
            p = subprocess.Popen(
                [cmd],
                stdin=subprocess.PIPE,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log_activity(
                self.user_avd.id,
                action_type="KillProcess",
                msg=f"Kill process of given port: {port}",
                error=None,
            )
            return True
        except Exception as e:
            log_activity(
                self.user_avd.id,
                action_type="KillProcessError",
                msg=f"Failed to kill process of given port: {port}",
                error=traceback.format_exc(),
            )
            return False

    def get_default_shadowsocks(self):
        socks = [
            "us-atl.prod.surfshark.com",
            "us-bdn.prod.surfshark.com",
            "us-bos.prod.surfshark.com",
            "us-buf.prod.surfshark.com",
            "us-chi.prod.surfshark.com",
            "us-clt.prod.surfshark.com",
            "us-dal.prod.surfshark.com",
            "us-den.prod.surfshark.com",
            "us-dtw.prod.surfshark.com",
            "us-hou.prod.surfshark.com",
            "us-kan.prod.surfshark.com",
            "us-las.prod.surfshark.com",
            "us-lax.prod.surfshark.com",
            "us-ltm.prod.surfshark.com",
            "us-mia.prod.surfshark.com",
            "us-mnz.prod.surfshark.com",
            "us-nyc-mp001.prod.surfshark.com",
            "us-nyc.prod.surfshark.com",
            "us-nyc-st001.prod.surfshark.com",
            "us-nyc-st002.prod.surfshark.com",
            "us-nyc-st003.prod.surfshark.com",
            "us-nyc-st004.prod.surfshark.com",
            "us-nyc-st005.prod.surfshark.com",
            "us-orl.prod.surfshark.com",
            "us-phx.prod.surfshark.com",
            "us-sea.prod.surfshark.com",
            "us-sfo-mp001.prod.surfshark.com",
            "us-sfo.prod.surfshark.com",
            "us-slc.prod.surfshark.com",
            "us-stl.prod.surfshark.com",
            "us-tpa.prod.surfshark.com",
        ]
        return socks

    def connect_shadowsocks(self, fail_tried=0):
        # check all required apk is installed
        self.check_apk_installation()

        # surfshark shadowsocks credentials
        proxy = self.user_avd.country
        port = "42578"
        password = "f6ueyEdH3TvvFn6HaevxKN7W"
        encryption_method = "AES-256-GCM"

        # click on home button
        self.driver().press_keycode(3)

        # start shadowsock app
        self.driver().start_activity("com.github.shadowsocks", ".MainActivity")

        # select first edited profile
        time.sleep(5)
        profile = (
            self.driver()
                .find_element_by_id("com.github.shadowsocks:id/container")
                .find_element_by_id("android:id/text1")
        )
        if not f"{proxy}:{port}" == profile.text:
            # click on edit button of first profile
            time.sleep(5)
            self.driver().find_elements_by_xpath(
                '//android.widget.ImageView[@content-desc="Edit"]'
            )[0].click()

            # proxy url input
            time.sleep(5)
            self.driver().find_elements_by_id("android:id/summary")[1].click()
            self.driver().find_element_by_id("android:id/edit").clear()
            self.driver().find_element_by_id("android:id/edit").send_keys(proxy)
            self.driver().find_element_by_id("android:id/button1").click()

            # proxy port input
            time.sleep(5)
            self.driver().find_elements_by_id("android:id/summary")[2].click()
            self.driver().find_element_by_id("android:id/edit").clear()
            self.driver().find_element_by_id("android:id/edit").send_keys(port)
            self.driver().find_element_by_id("android:id/button1").click()

            # filling proxy password
            time.sleep(5)
            self.driver().find_elements_by_id("android:id/summary")[3].click()
            self.driver().find_element_by_id("android:id/edit").clear()
            self.driver().find_element_by_id("android:id/edit").send_keys(password)
            self.driver().find_element_by_id("android:id/button1").click()

            # select encryption method
            option = False
            for x in range(4):
                time.sleep(5)
                enc_method = self.driver().find_elements_by_id("android:id/summary")[4]
                if enc_method.text == encryption_method:
                    break
                enc_method.click()
                time.sleep(5)
                options = self.driver().find_elements_by_id("android:id/text1")
                for option in options:
                    if option.text == "AES-256-GCM":
                        break
                option.click()

            # click  save profile button
            time.sleep(5)
            self.driver().find_element_by_id(
                "com.github.shadowsocks:id/action_apply"
            ).click()

            # select first edited profile
            profile = (
                self.driver()
                    .find_element_by_id("com.github.shadowsocks:id/container")
                    .find_element_by_id("android:id/text1")
            )

        # click on profile
        if profile.text == f"{proxy}:{port}":
            profile.click()

        # connect button
        time.sleep(5)
        self.driver().find_elements_by_class_name("android.widget.ImageButton")[
            1
        ].click()

        # press ok button if popup exists
        time.sleep(5)
        ok_btn = self.driver().find_elements_by_id("android:id/button1")
        if len(ok_btn):
            ok_btn[0].click()

        time.sleep(5)
        for i in range(5):
            time.sleep(2)
            connection_status = self.driver().find_element_by_id(
                "com.github.shadowsocks:id/status"
            )
            if connection_status.text == "Connected, tap to check connection":
                connection_status.click()
                time.sleep(5)
                connection_status = self.driver().find_element_by_id(
                    "com.github.shadowsocks:id/status"
                )
                if "Success" in connection_status.text:
                    print("VPN STATUS: CONNECTED!")
                    log_activity(
                        self.user_avd.id,
                        action_type="ConnectShadowsock",
                        msg=f"Shadowsock connected successfully",
                        error=None,
                    )
                    return True
                else:
                    disconnect_btn_id = self.driver().find_elements_by_id(
                        "com.github.shadowsocks:id/fab"
                    )
                    disconnect_btn_xpath = self.driver().find_elements_by_xpath(
                        '//android.widget.ImageButton[@content-desc="Stop"]'
                    )
                    disconnect_btn = disconnect_btn_id or disconnect_btn_xpath
                    disconnect_btn[0].click()
                    time.sleep(1)

                    connect_btn_id = self.driver().find_elements_by_id(
                        "com.github.shadowsocks:id/fab"
                    )
                    connect_btn_xpath = self.driver().find_elements_by_xpath(
                        '//android.widget.ImageButton[@content-desc="Connect"]'
                    )
                    connect_btn = connect_btn_id or connect_btn_xpath
                    connect_btn[0].click()
                    time.sleep(1)

            else:
                print("VPN STATUS: Invalid Settings.")
                log_activity(
                    self.user_avd.id,
                    action_type="ConnectSNordVpnError",
                    msg=f"Failed to connect NordVPN",
                    error="VPN STATUS: Invalid Settings.",
                )

        print("VPN STATUS: Network Issue.")
        log_activity(
            self.user_avd.id,
            action_type="ConnectNordVpnError",
            msg=f"Failed to connect NordVPN",
            error="VPN STATUS: Network Issue.",
        )
        fail_tried += 1
        if fail_tried <= 3:
            socket = random.choice(NordVpn.get_server_list())
            self.user_avd.country = socket
            self.user_avd.save()
            self.connect_shadowsocks(fail_tried=fail_tried)

        return False

    def logout_twitter(self):
        restart_app(self.driver, "twitter")

        # check if captcha confirmation
        time.sleep(5)
        captcha_ele_one = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("What happened?")'
        )
        captcha_ele_two = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Are you a robot?")'
        )
        captcha_ele = captcha_ele_one or captcha_ele_two
        if captcha_ele:
            options_btn_id = self.driver().find_elements_by_id("More options")
            options_btn_xpath = self.driver().find_elements_by_xpath(
                '//android.widget.ImageView[@content-desc="More options"]'
            )
            options_btn = options_btn_id or options_btn_xpath
            options_btn[0].click()

            time.sleep(2)

            signout_btn_xpath1 = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[2]/android.widget.LinearLayout"
            )
            signout_btn_xpath2 = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[2]/android.widget.LinearLayout/android.widget.RelativeLayout/android.widget.TextView"
            )
            signout_btn = signout_btn_xpath1 or signout_btn_xpath2
            signout_btn[0].click()

            time.sleep(2)

            signout_confirm_btn_id = self.driver().find_elements_by_id(
                "android:id/button1"
            )
            signout_confirm_btn_xpath = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[2]"
            )
            signout_confirm_btn = signout_confirm_btn_id or signout_confirm_btn_xpath
            signout_confirm_btn[0].click()

            time.sleep(2)
            return True

        # check if already logged in or not.
        ele_one = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]'
        )
        ele_two = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View'
        )
        ele_three = self.driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab. New items"]'
        )

        home_btn = ele_one or ele_two or ele_three
        if home_btn:
            try:
                drawer_btn_xpath = self.driver().find_elements_by_xpath(
                    '//android.widget.ImageButton[@content-desc="Show navigation drawer"]'
                )
                drawer_btn_id = self.driver().find_elements_by_accessibility_id(
                    "Show navigation drawer"
                )

                drawer_btn = drawer_btn_id or drawer_btn_xpath
                drawer_btn[0].click()

                settings_btn = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[6]/android.widget.TextView"
                )
                settings_btn[0].click()

                acc_btn_xpath_one = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[1]/android.widget.RelativeLayout/android.widget.TextView"
                )
                acc_btn_xpath_two = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[1]/android.widget.RelativeLayout"
                )
                acc_btn_xpath_three = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[1]"
                )

                acc_btn = acc_btn_xpath_two or acc_btn_xpath_one or acc_btn_xpath_three
                acc_btn[0].click()
                time.sleep(2)

                self.driver().swipe(
                    start_x=random.randrange(50, 100),
                    start_y=random.randrange(400, 500),
                    end_x=random.randrange(50, 100),
                    end_y=0,
                    duration=random.randrange(650, 850),
                )

                logout_btn_xpath_one = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[8]/android.widget.RelativeLayout/android.widget.TextView"
                )
                logout_btn_xpath_two = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[8]/android.widget.RelativeLayout"
                )
                logout_btn_xpath_three = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[8]"
                )
                logout_btn = (
                        logout_btn_xpath_one
                        or logout_btn_xpath_two
                        or logout_btn_xpath_three
                )
                logout_btn[0].click()

                confirm_logout_id = self.driver().find_elements_by_id(
                    "android:id/button1"
                )
                confirm_logout_xpath = self.driver().find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[2]"
                )

                confirm_logout = confirm_logout_id or confirm_logout_xpath
                confirm_logout[0].click()
                time.sleep(5)
                return True
            except Exception as e:
                print(e)
                return False

        else:
            return True

    def perform_login(self):
        if self.service.is_running and self.service.is_listening:
            # goto home page
            self.driver().press_keycode(3)
            time.sleep(3)

            # get details from twitter account
            twitter_account = self.user_avd.twitter_account
            username = twitter_account.phone if not twitter_account.screen_name else twitter_account.screen_name
            password = twitter_account.password

            # launch target app ( twitter )
            start_app(self.driver, "twitter")

            if (
                    not self.driver().current_activity
                        == "com.twitter.app.main.MainActivity"
            ):
                # click on login btn
                for x in range(10):
                    x_axis = 225
                    y_axis = 600 - x * 10
                    TouchAction(self.driver()).tap(x=x_axis, y=y_axis).perform()
                    time.sleep(2)
                    if self.driver().current_activity == ".LoginActivity":
                        break

                # perform login action
                time.sleep(2)
                self.driver().find_element_by_id("com.twitter.android:id/login_identifier").send_keys(username)
                time.sleep(2)
                self.driver().find_element_by_id(
                    "com.twitter.android:id/login_password"
                ).send_keys(password)
                time.sleep(2)
                self.driver().find_element_by_id(
                    "com.twitter.android:id/login_login"
                ).click()
                # com.twitter.app.main.MainActivity
                for x in range(5):
                    print(f"*** checking main page load with wait: {x}sec")
                    if self.driver().current_activity == "com.twitter.app.main.MainActivity":
                        break
                    else:
                        time.sleep(x)

                log_activity(
                    self.user_avd.id,
                    action_type="LoginAccount",
                    msg=f"Logged in successfully for {self.user_avd.name}",
                    error=None,
                )
            else:
                log_activity(
                    self.user_avd.id,
                    action_type="LoginAccount",
                    msg=f"Already login skipped steps for {self.user_avd.name}",
                    error=None,
                )

            print("*** login process completed. ***")
        else:
            log_activity(
                self.user_avd.id,
                action_type="LoginAccount",
                msg=f"Skipped login appium service not running",
                error=None
            )

    def create_account_twitter(self, full_name, password, phone):
        """
        create_account_twitter: creates twitter account with given user details.

        args:
        full_name: user full name
        password: user password
        phone: united state phone number
        """
        self.phone = phone
        start_app(self.driver, "twitter")

        # Find and click on Create Account button
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
        create_account_btn[0].click()

        # Find name field and fill with full name
        name_field_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/name_field"
        )
        name_field_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[1]"
        )
        name_field = name_field_id or name_field_xpath
        name_field[0].send_keys(full_name)
        time.sleep(4)

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
        phone_field[0].click()
        phone_field[0].send_keys("+" + phone)
        press_enter(self.driver)
        time.sleep(4)

        # Scroll to select random date of birth
        birthday_field_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/birthday_field"
        )
        birthday_field_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[3]"
        )
        birthday_field = birthday_field_id or birthday_field_xpath
        if birthday_field:
            birthday_field[0].click()
        else:
            press_enter(self.driver)

        # Random birth date selection with swipe
        for i in range(random.randint(17, 20)):
            self.driver().swipe(
                start_x=80,
                start_y=500,
                end_x=80,
                end_y=575,
                duration=random.randrange(650, 850),
            )
            self.driver().swipe(
                start_x=160,
                start_y=500,
                end_x=125,
                end_y=575,
                duration=random.randrange(650, 850),
            )
            self.driver().swipe(
                start_x=240,
                start_y=500,
                end_x=240,
                end_y=575,
                duration=random.randrange(650, 850),
            )

        # Click on next button
        next_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        next_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout"
            "/android.widget.RelativeLayout/android.widget.Button"
        )
        next_btn = next_btn_id or next_btn_xpath
        next_btn[0].click()
        time.sleep(4)
        next_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        next_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup"
            "/android.widget.Button"
        )
        next_btn = next_btn_id or next_btn_xpath
        next_btn[0].click()
        time.sleep(4)

        # Click on signup button
        signup_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        signup_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.Button"
        )
        signup_btn = signup_btn_id or signup_btn_xpath
        signup_btn[0].click()
        time.sleep(4)

        # Click on verify button
        verify_phone_btn_id = self.driver().find_elements_by_id("android:id/button1")
        verify_phone_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[2]"
        )
        verify_phone_btn = verify_phone_btn_id or verify_phone_btn_xpath
        verify_phone_btn[0].click()
        time.sleep(4)

        # Check if number is active and can receive otp otherwise ban
        verify_code_field_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/text_field"
        )
        verify_code_field_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.view.ViewGroup/android.widget.LinearLayout/android.widget.EditText"
        )
        verify_code_field = verify_code_field_id or verify_code_field_xpath
        if not verify_code_field:
            ban_twitter_number(phone.replace("+", ""))
            print("*** Failed to get verification field ***")
            return False
        otp = get_twitter_sms(phone.replace("+", ""))
        if not otp:
            ban_twitter_number(phone.replace("+", ""))
            print("*** Failed to get otp ***")
            return False
        verify_code_field[0].send_keys(otp)
        # self.driver().implicitly_wait(10)
        time.sleep(4)

        # After verification of security code click on signup button
        signup_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        signup_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.Button"
        )
        signup_btn = signup_btn_id or signup_btn_xpath
        signup_btn[0].click()
        time.sleep(4)

        # Fill user password in password field
        password_field_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/text_field"
        )
        password_field_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.view.ViewGroup/android.widget.LinearLayout/android.widget.EditText"
        )
        password_field = password_field_id or password_field_xpath
        password_field[0].send_keys(password)
        time.sleep(4)

        # Click on next buttons
        next_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        next_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.Button"
        )
        next_btn = next_btn_id or next_btn_xpath
        next_btn[0].click()
        time.sleep(4)

        # Click on skip buttons
        skip_dp_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/secondary_button"
        )
        skip_dp_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup"
            "/android.widget.TextView"
        )
        skip_dp_btn = skip_dp_btn_id or skip_dp_btn_xpath
        skip_dp_btn[0].click()
        time.sleep(4)
        skip_bio_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/secondary_button"
        )
        skip_bio_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup"
            "/android.widget.TextView"
        )
        skip_bio_btn = skip_bio_btn_id or skip_bio_btn_xpath
        skip_bio_btn[0].click()
        time.sleep(4)

        # Click on don't sync button
        dont_sync_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/button_negative"
        )
        dont_sync_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.ScrollView/android.view.ViewGroup/android.widget.LinearLayout/android.widget.Button[2]"
        )
        dont_sync_btn = dont_sync_btn_id or dont_sync_btn_xpath
        dont_sync_btn[0].click() if dont_sync_btn else None
        time.sleep(4)

        # Click on next button
        next_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        next_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android"
            ".widget.Button"
        )
        next_btn = next_btn_id or next_btn_xpath
        next_btn[0].click()
        time.sleep(4)
        # Follow accounts
        follow_btns = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/follow_button")'
        )
        if follow_btns:
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
                duration=duration
            )
            follow_btns = self.driver().find_elements_by_android_uiautomator(
                'new UiSelector().resourceId("com.twitter.android:id/follow_button")'
            )
            random.shuffle(follow_btns) if follow_btns else None
            for btn in follow_btns:
                time.sleep(random.randint(1, 3))
                btn.click()
        # Click on next button
        next_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        next_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android"
            ".widget.Button"
        )
        next_btn = next_btn_id or next_btn_xpath
        next_btn[0].click() if next_btn else None
        time.sleep(4)

        # Follow accounts
        follow_btns = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().resourceId("com.twitter.android:id/follow_button")'
        )
        if follow_btns:
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
                duration=duration
            )
            random.shuffle(follow_btns)
            for btn in follow_btns:
                time.sleep(random.randint(1, 3))
                btn.click()

        next_btn = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("NEXT")'
        )
        next_btn[0].click() if next_btn else None

        next_btn_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/cta_button"
        )
        next_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android"
            ".widget.Button"
        )
        next_btn = next_btn_id or next_btn_xpath
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        done_btn = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("DONE")'
        )
        done_btn[0].click() if done_btn else None
        time.sleep(5)
        restart_app(self.driver, 'twitter')
        ok_btn = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("OK")'
        )
        ok_btn[0].click() if ok_btn else None
        time.sleep(5)
        # Save created account details as twitter account in db
        drawer_btn_id = self.driver().find_elements_by_id("Show navigation drawer")
        drawer_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show navigation drawer"]'
        )
        drawer_btn = drawer_btn_id or drawer_btn_xpath
        drawer_btn[0].click()
        username = (
            self.driver()
                .find_elements_by_id("com.twitter.android:id/username")[0]
                .text.replace("@", "")
        )
        print(
            f"""
        Username: {username}
        Password: {password}
        Phone: {phone}
        """
        )
        return username

    def bypass_captcha(self):
        # check if captcha confirmation
        captcha_ele_one = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("What happened?")'
        )
        captcha_ele_two = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("What next?")'
        )
        captcha_ele_three = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Are you a robot?")'
        )
        captcha_ele = captcha_ele_one or captcha_ele_two or captcha_ele_three
        if captcha_ele:
            try:
                next_btn_xpath1 = self.app_driver.find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout"
                    "/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android"
                    ".widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View["
                    "8]/android.widget.Button "
                )
                next_btn_2 = self.app_driver.find_elements_by_android_uiautomator(
                    'new UiSelector().text("Start")'
                )
                next_btn = next_btn_xpath1 or next_btn_2
                next_btn[0].click()
            except:
                pass

            # click on I am not robot checkbox
            try:
                captcha_checkbox_id = self.app_driver.find_elements_by_id(
                    "recaptcha-anchor"
                )
                captcha_checkbox_xpath = self.app_driver.find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout"
                    "/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android"
                    ".widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View["
                    "2]/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View["
                    "2]/android.view.View[1]/android.view.View/android.widget.CheckBox "
                )
                captcha_checkbox = captcha_checkbox_id or captcha_checkbox_xpath
                captcha_checkbox[0].click()
            except:
                self.app_driver.tap(
                    [(random.randrange(25, 53), random.randrange(170, 198))]
                )
            time.sleep(3)

            # click on audio button
            try:
                captcha_audio_id = self.app_driver.find_elements_by_id(
                    "recaptcha-audio-button"
                )
                captcha_audio_xpath = self.app_driver.find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout"
                    "/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android"
                    ".widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View["
                    "3]/android.view.View[2]/android.view.View/android.view.View/android.view.View/android.view.View["
                    "3]/android.view.View[2]/android.widget.Button "
                )
                captcha_audio_btn = captcha_audio_id or captcha_audio_xpath
                captcha_audio_btn[0].click()
            except:
                self.app_driver.tap(
                    [(random.randrange(55, 103), random.randrange(538, 586))]
                )
            time.sleep(3)

            # increase volume
            for i in range(10):
                self.app_driver.press_keycode(24)

            for i in range(3):

                # start recording
                for i in range(3):
                    record_process = start_recording()

                    # play audio captcha
                    try:
                        play_btn_id = self.app_driver.find_elements_by_id(":3")
                        play_btn_xpath = self.app_driver.find_elements_by_xpath("")
                        play_btn = play_btn_id or play_btn_xpath
                        play_btn[0].click()
                    except:
                        self.app_driver.tap(
                            [(random.randrange(40, 280), random.randrange(127, 169))]
                        )
                    time.sleep(5)

                    # Stop recording
                    stop_recording(record_process)

                    # call google speech to text api or method here to get captcha result in text
                    audio = load_audio()
                    result_text = audio_to_text(audio)

                    if result_text:
                        break
                    else:
                        # reload captcha
                        try:
                            reload_captcha_btn_id = self.app_driver.find_elements_by_id(
                                "recaptcha-reload-button"
                            )
                            reload_captcha_btn_xpath = self.app_driver.find_elements_by_xpath(
                                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget"
                                ".FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget"
                                ".LinearLayout/android.widget.FrameLayout/android.webkit.WebView/android.webkit"
                                ".WebView/android.view.View[3]/android.view.View["
                                "2]/android.view.View/android.view.View/android.view.View[4]/android.view.View["
                                "1]/android.widget.Button "
                            )
                            reload_captcha_btn = (
                                    reload_captcha_btn_id or reload_captcha_btn_xpath
                            )
                            reload_captcha_btn[0].click()
                        except:
                            self.app_driver.tap(
                                [(random.randrange(26, 74), random.randrange(270, 318))]
                            )
                        time.sleep(2)

                # enter result text into audio response field
                audio_response_field_id = self.app_driver.find_elements_by_id(
                    "audio-response"
                )
                audio_response_field_xpath = self.app_driver.find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout"
                    "/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android"
                    ".widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View["
                    "3]/android.view.View[2]/android.view.View/android.view.View/android.view.View["
                    "3]/android.widget.EditText "
                )
                audio_response_field = (
                        audio_response_field_id or audio_response_field_xpath
                )
                audio_response_field[0].send_keys(result_text)

                # click of verify button
                verify_button_id = self.app_driver.find_elements_by_id(
                    "recaptcha-verify-button"
                )
                verify_button_xpath = self.app_driver.find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout"
                    "/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android"
                    ".widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View["
                    "3]/android.view.View[2]/android.view.View/android.view.View/android.view.View["
                    "4]/android.view.View[4]/android.widget.Button "
                )
                verify_button = verify_button_id or verify_button_xpath
                verify_button[0].click()
                time.sleep(3)

                # check if captcha failed
                captcha_failed_xpath = self.app_driver.find_elements_by_xpath(
                    "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout"
                    "/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android"
                    ".widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View["
                    "3]/android.view.View[2]/android.view.View/android.view.View/android.view.View[1] "
                )
                captcha_failed = self.app_driver.find_elements_by_android_uiautomator(
                    'new UiSelector().text("Multiple correct solutions required - please solve more.")'
                )
                captcha_failed_msg = captcha_failed or captcha_failed_xpath
                if not captcha_failed_msg:
                    try:
                        continue_btn_id = self.app_driver.find_elements_by_id(
                            "continue_button"
                        )
                        continue_btn_xpath = self.app_driver.find_elements_by_xpath(
                            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget"
                            ".FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget"
                            ".LinearLayout/android.widget.FrameLayout/android.webkit.WebView/android.webkit.WebView"
                            "/android.view.View[2]/android.widget.Button "
                        )
                        continue_btn = continue_btn_id or continue_btn_xpath
                        continue_btn[0].click()

                        try:
                            continue_to_twitter_xpath = self.app_driver.find_elements_by_xpath(
                                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget"
                                ".FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget"
                                ".LinearLayout/android.widget.FrameLayout/android.webkit.WebView/android.webkit"
                                ".WebView/android.view.View[4]/android.widget.Button "
                            )
                            continue_to_twitter_xpath[0].click()
                        except:
                            self.app_driver.tap(
                                [
                                    (
                                        random.randrange(12, 167),
                                        random.randrange(257, 291),
                                    )
                                ]
                            )

                    except:
                        self.app_driver.tap(
                            [(random.randrange(12, 250), random.randrange(103, 284))]
                        )
                    continue_button = (
                        self.app_driver.find_elements_by_android_uiautomator(
                            'new UiSelector().text("Continue to Twitter")'
                        )
                    )
                    if len(continue_button):
                        continue_button[0].click()

                    return True

                else:
                    # reload captcha
                    try:
                        reload_captcha_btn_id = self.app_driver.find_elements_by_id(
                            "recaptcha-reload-button"
                        )
                        reload_captcha_btn_xpath = self.app_driver.find_elements_by_xpath(
                            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget"
                            ".FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget"
                            ".LinearLayout/android.widget.FrameLayout/android.webkit.WebView/android.webkit.WebView"
                            "/android.view.View[3]/android.view.View["
                            "2]/android.view.View/android.view.View/android.view.View[5]/android.view.View["
                            "1]/android.widget.Button "
                        )
                        reload_captcha_btn = (
                                reload_captcha_btn_id or reload_captcha_btn_xpath
                        )
                        reload_captcha_btn[0].click()
                    except:
                        self.app_driver.tap(
                            [(random.randrange(26, 74), random.randrange(322, 370))]
                        )
                    time.sleep(2)
            log_activity(
                self.user_avd.id,
                action_type="CaptchaVerification",
                msg=f"Failed to verify Google captcha for {self.user_avd.name}",
                error=None,
            )
            return False

    def profile_setup_or_update(self):
        twitter_account = self.user_avd.twitter_account
        full_name = twitter_account.full_name
        bio = twitter_account.bio
        profile_image_url = twitter_account.profile_image
        banner_image_url = twitter_account.banner_image
        location = twitter_account.location

        # download profile image
        download_image(url=profile_image_url, image_name="profile_image.jpg")
        file_path = os.path.join(BASE_DIR, "images/profile_image.jpg")

        # delete all files in download folder
        delete_download_files(self.emulator_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.emulator_port)

        ok_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("OK")')
        ok_btn[0].click() if ok_btn else None

        # go to edit profile
        navigation_btn_id = self.driver().find_elements_by_id("Show navigation drawer")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show navigation drawer"]'
        )
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        navigation_btn[0].click() if navigation_btn else None
        time.sleep(2)

        profile_btn_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget"
            ".FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout[1] "
        )
        profile_btn_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget"
            ".FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.LinearLayout["
            "1]/android.widget.TextView "
        )
        profile_btn = profile_btn_xpath1 or profile_btn_xpath2
        profile_btn[0].click() if profile_btn else None
        for x in range(5):
            print(f"*** checking profile page load with wait: {x}sec")
            if self.driver().current_activity == "com.twitter.app.profiles.ProfileActivity":
                break
            else:
                time.sleep(x)
        print(self.driver().current_activity)
        time.sleep(2)
        edit_profile_btn = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("EDIT PROFILE")'
        )
        self.update_account(self.user_avd.twitter_account) if edit_profile_btn else self.setup_account()
        time.sleep(2)

    def setup_account(self):
        twitter_account = self.user_avd.twitter_account
        full_name = twitter_account.full_name
        bio = twitter_account.bio
        profile_image_url = twitter_account.profile_image
        banner_image_url = twitter_account.banner_image
        location = twitter_account.location

        edit_profile_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/button_edit_profile")
        edit_profile_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android"
            ".widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.FrameLayout["
            "1]/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.Button "
        )
        edit_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("SETUP PROFILE")')
        edit_profile_btn = edit_btn or edit_profile_btn_id or edit_profile_btn_xpath
        edit_profile_btn[0].click()
        time.sleep(5)

        # download profile image
        download_image(url=profile_image_url, image_name="profile_image.jpg")
        file_path = os.path.join(BASE_DIR, "images/profile_image.jpg")

        # delete all files in download folder
        delete_download_files(self.emulator_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.emulator_port)

        upload_image = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Upload")')
        upload_image[0].click() if upload_image else None

        choose_photo = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Choose existing photo")')
        choose_photo[0].click() if upload_image else None

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        navigation_btn_id = self.driver().find_elements_by_accessibility_id("Show roots")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]')
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        navigation_btn[0].click() if navigation_btn else None
        time.sleep(5)

        download_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Downloads")')

        if len(download_btn) == 2:
            download_btn[1].click()
        else:
            download_btn[0].click()

        time.sleep(5)

        # Select Image
        image_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout ")
        image_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1] ")
        image = image_xpath1 or image_xpath2
        image[0].click() if image else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        # download profile image
        download_image(url=banner_image_url, image_name="banner_image.jpg")
        file_path = os.path.join(BASE_DIR, "images/banner_image.jpg")

        # delete all files in download folder
        delete_download_files(self.emulator_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.emulator_port)

        upload_image = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Upload")')
        upload_image[0].click() if upload_image else None

        choose_photo = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Choose existing photo")')
        choose_photo[0].click() if upload_image else None

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        navigation_btn_id = self.driver().find_elements_by_accessibility_id("Show roots")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]')
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        navigation_btn[0].click() if navigation_btn else None
        time.sleep(5)

        download_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Downloads")')

        if len(download_btn) == 2:
            download_btn[1].click()
        else:
            download_btn[0].click()

        time.sleep(5)

        # Select Image
        image_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout ")
        image_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1] ")
        image = image_xpath1 or image_xpath2
        image[0].click() if image else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        edit_btn = self.driver().find_elements_by_class_name('android.widget.EditText')
        edit_btn[0].click() if edit_btn else None

        edit_btn = self.driver().find_elements_by_class_name('android.widget.EditText')
        edit_btn[0].send_keys(bio) if edit_btn else None

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        skip_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Skip for now")')
        skip_btn[0].click() if skip_btn else None
        time.sleep(5)

        see_profile = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("SEE PROFILE")')
        see_profile[0].click() if see_profile else None
        time.sleep(5)

    def update_account(self, twitter_account):
        full_name = twitter_account.full_name
        bio = twitter_account.bio
        profile_image_url = twitter_account.profile_image
        banner_image_url = twitter_account.banner_image
        location = twitter_account.location

        edit_profile_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/button_edit_profile")
        edit_profile_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android"
            ".widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.FrameLayout["
            "1]/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.Button "
        )
        edit_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("EDIT PROFILE")')
        edit_profile_btn = edit_btn or edit_profile_btn_id or edit_profile_btn_xpath
        edit_profile_btn[0].click()
        time.sleep(2)
        #
        # # update name
        # name_field_id = self.driver().find_elements_by_id(
        #     "com.twitter.android:id/edit_name"
        # )
        # name_field_xpath = self.driver().find_elements_by_xpath(
        #     "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
        #     ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
        #     "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[1] "
        # )
        # name_field = name_field_id or name_field_xpath
        # name_field[0].clear()
        # name_field[0].send_keys(full_name)
        # time.sleep(2)
        #
        # # update bio
        # bio_field_id = self.driver().find_elements_by_id("com.twitter.android:id/edit_bio")
        # bio_field_xpath = self.driver().find_elements_by_xpath(
        #     "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
        #     ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
        #     "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[2] "
        # )
        # bio_field = bio_field_id or bio_field_xpath
        # bio_field[0].clear()
        # bio_field[0].send_keys(bio)
        # time.sleep(2)
        #
        # set new profile pic
        set_image_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/avatar_image"
        )
        set_image_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
            "/android.widget.RelativeLayout/android.widget.FrameLayout[2] "
        )
        set_image = set_image_id or set_image_xpath
        set_image[0].click()
        time.sleep(2)

        continue_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("CONTINUE")')
        continue_btn[0].click() if continue_btn else None

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        allow_btn[0].click() if allow_btn else None

        choose_existing_photo = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.LinearLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.TextView[2] "
        )
        choose_existing_photo[0].click()
        time.sleep(2)

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        allow_btn[0].click() if allow_btn else None

        navigation_btn_id = self.driver().find_elements_by_accessibility_id("Show roots")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]'
        )
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        navigation_btn[0].click()
        time.sleep(2)

        download_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Downloads")')

        if len(download_btn) == 2:
            download_btn[1].click()
        else:
            download_btn[0].click()

        # allow media access
        dialog_title_id = self.driver().find_elements_by_id(
            "com.twitter.android:id/dialog_title"
        )
        dialog_title_xpath = self.driver().find_elements_by_xpath(
            '//android.view.ViewGroup[@content-desc="To attach media, we need access to your gallery,'
            '"]/android.widget.TextView '
        )
        dialog_title = dialog_title_id or dialog_title_xpath
        if dialog_title:
            continue_btn_id = self.driver().find_elements_by_id(
                "com.twitter.android:id/permissions_button_positive"
            )
            continue_btn_xpath = self.driver().find_elements_by_xpath(
                '//android.view.ViewGroup[@content-desc="To attach media, we need access to your gallery,'
                '"]/android.widget.Button '
            )
            continue_btn = continue_btn_id or continue_btn_xpath
            continue_btn[0].click()
            time.sleep(2)

            allow_btn_id = self.driver().find_elements_by_id(
                '//android.view.ViewGroup[@content-desc="To attach media, we need access to your gallery,'
                '"]/android.widget.Button '
            )
            allow_btn_xpath = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android"
                ".view.ViewGroup/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout"
                "/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.Button[2] "
            )
            allow_btn = allow_btn_id or allow_btn_xpath
            if allow_btn:
                allow_btn[0].click()
                time.sleep(2)

        # Select Image
        image_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout ")
        image_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1] ")
        image = image_xpath1 or image_xpath2
        image[0].click()
        time.sleep(2)

        done_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/done")
        done_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout"
            "/android.widget.FrameLayout[2]/android.widget.TextView "
        )
        done_btn = done_btn_id or done_btn_xpath
        done_btn[0].click() if done_btn else None
        time.sleep(2)

        # download profile image
        download_image(url=banner_image_url, image_name="banner_image.jpg")
        file_path = os.path.join(BASE_DIR, "images/banner_image.jpg")

        # delete all files in download folder
        delete_download_files(self.emulator_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.emulator_port)

        # set banner
        banner_id = self.driver().find_elements_by_accessibility_id(
            "Overlay for avatar"
        )
        banner_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageView[@content-desc="Overlay for avatar"]'
        )
        banner = banner_id or banner_xpath
        banner[0].click()
        time.sleep(2)

        # choose existing photo
        existing_photo = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.LinearLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.TextView[2] "
        )
        existing_photo[0].click()
        time.sleep(2)

        # select image
        image_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view"
            ".ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout"
            "/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view"
            ".ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout "
        )
        image_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view"
            ".ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout"
            "/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view"
            ".ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1] "
        )
        image = image_xpath1 or image_xpath2
        image[0].click() if image else None
        time.sleep(2)

        done_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/done")
        done_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout"
            "/android.widget.FrameLayout[2]/android.widget.TextView "
        )
        done_btn = done_btn_id or done_btn_xpath
        done_btn[0].click() if done_btn else None
        time.sleep(2)

        # save all changes
        save_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/save")
        save_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup"
            "/androidx.appcompat.widget.LinearLayoutCompat/android.widget.TextView "
        )
        save_btn = save_btn_id or save_btn_xpath
        save_btn[0].click()
        time.sleep(2)

        for x in range(5):
            print(f"*** checking profile page load with wait: {x}sec")
            if self.driver().current_activity == "com.twitter.app.profiles.ProfileActivity":
                break
            else:
                time.sleep(x)

        not_now_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NOT NOW")')
        not_now_btn[0].click() if not_now_btn else None

        # delete all image in local folder
        images_folder = os.path.join(BASE_DIR, "images/*")
        del_cmd = f"rm -r {images_folder}"
        process = subprocess.Popen(
            [del_cmd],
            stdin=subprocess.PIPE,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.wait()
        log_activity(
            self.user_avd.id,
            action_type="ProfileUpdation",
            msg=f"Profile updated for {self.user_avd.name}",
            error=None,
        )

    def kill_current_process(self):
        if self.service.is_running:
            self.service.stop()
            print("*** Stopped appium server ***")
        if self.device:
            self.device.terminate()
            print("*** Terminated emulator ***")

    def wait_activity(self, activity, timeout, interval=1):
        """Wait for an activity: block until target activity presents
        or time out.

        This is an Android-only method.

        :Agrs:
         - activity - target activity
         - timeout - max wait time, in seconds
         - interval - sleep interval between retries, in seconds
        """
        try:
            WebDriverWait(self.app_driver, timeout, interval).until(
                lambda d: d.current_activity == activity
            )
            return True
        except TimeoutException:
            return False

    def perform_verification(self):
        """
        Identify and verify verification: check which verification asked by twitter and
        verify.
        """
        continue_btn = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Continue to Twitter")'
        )
        continue_btn[0].click() if continue_btn else None

        code_element = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("Didn\'t receive a code?")'
        )
        code_element[0].click() if code_element else None

        phone_verification_text = (
            "Verify your identity by entering the phone number associated "
            "with your Twitter account."
        )
        elements = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("{phone_verification_text}")'
        )

        are_you_robot = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Are you a robot?")'
        )

        if len(elements):
            self.verify_phone_number()

        captcha_verificatoin_text = "Pass a Google reCAPTCHA challenge"
        phone_verification_text = "Verify your phone number"
        captcha_element = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("{captcha_verificatoin_text}")'
        )
        captcha_element_2 = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("To get back to the Tweets, select Start to verify you\'re really human.")'
        )
        phone_element = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("{phone_verification_text}")'
        )
        if captcha_element and phone_element:
            log_activity(
                self.user_avd.id,
                action_type="CaptchaAndPhoneVerification",
                msg=f"Twitter Asked for captcha and phone verification for {self.user_avd.name}",
                error=None,
            )
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(5)
            self.bypass_captcha()
            log_activity(
                self.user_avd.id,
                action_type="CaptchaVerification",
                msg=f"Google Capcha verified successfully for {self.user_avd.name}",
                error=None,
            )
            # Phone verification
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(3)
            send_code_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Send code")')
            send_code_btn[0].click() if send_code_btn else None
            get_twitter_number(mobile=self.phone)
            code = get_twitter_sms(phone_number=self.phone)
            confirmation_input = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Enter confirmation code")'
            )
            confirmation_input[0].clear() if confirmation_input else None
            confirmation_input[0].send_keys(code) if confirmation_input else None
            next_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Next")')
            next_btn[0].click() if next_btn else None
            continue_btn = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Continue to Twitter")'
            )
            continue_btn[0].click() if continue_btn else None
            log_activity(
                self.user_avd.id,
                action_type="PhoneVerification",
                msg=f"Phone number verified successfully for {self.user_avd.name}",
                error=None,
            )
        elif captcha_element or captcha_element_2 or are_you_robot:
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(5)
            self.bypass_captcha()
            log_activity(
                self.user_avd.id,
                action_type="OnlyCaptchaVerification",
                msg=f"Google captcha verified successfully for {self.user_avd.name}",
                error=None,
            )
        elif phone_element or code_element:
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(3)
            send_code_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Send code")')
            send_code_btn[0].click() if send_code_btn else None
            get_twitter_number(mobile=self.phone)
            code = get_twitter_sms(phone_number=self.phone)
            confirmation_input = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Enter confirmation code")'
            )
            confirmation_input[0].clear() if confirmation_input else None
            confirmation_input[0].send_keys(code) if confirmation_input else None
            next_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Next")')
            next_btn[0].click() if next_btn else None
            continue_btn = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Continue to Twitter")'
            )
            continue_btn[0].click() if continue_btn else None
            log_activity(
                self.user_avd.id,
                action_type="OnlyPhoneVerification",
                msg=f"Phone number verified successfully for {self.user_avd.name}",
                error=None,
            )

    def verify_phone_number(self):
        """
        Phone number verification: Check and Confirm phone verification asked by
        twitter account.

        This is an Android-only method.
        """
        self.app_driver.find_elements_by_class_name(
            "android.widget.EditText"
        )[0].send_keys(self.user_avd.twitter_account.phone)
        self.app_driver.find_elements_by_class_name(
            "android.widget.Button"
        )[0].click()
        print("*** Phone number verification completed ***")
        log_activity(
            self.user_avd.id,
            action_type="PhoneVerification",
            msg=f"Twitter Matched phone number with saved one.",
            error=None,
        )

    def kill_bot_process(self, appium=False, emulators=False):
        try:
            # Kill all running appium instances
            # if appium:
            #     kill_cmd = "kill -9 $(pgrep -f appium)"
            #     kill_process = subprocess.Popen(
            #         [kill_cmd],
            #         stdout=subprocess.PIPE,
            #         stderr=subprocess.PIPE,
            #         shell=True,
            #     )
            #     kill_process.wait()
            # 
            #     kill_cmd = "fuser -k -n tcp 4724"
            #     kill_process = subprocess.Popen(
            #         [kill_cmd],
            #         stdout=subprocess.PIPE,
            #         stderr=subprocess.PIPE,
            #         shell=True,
            #     )
            #     kill_process.wait()
            #     log_activity(
            #         self.user_avd.id,
            #         action_type="KillAppiumServer",
            #         msg=f"Killed appium server for {self.user_avd.name}",
            #         error=None,
            #     )

            # Kill All emulators
            if emulators:
                self.device = None
                process_names = [
                    "qemu-system-x86_64",
                    "emulator64-crash-service",
                    "adb",
                ]
                for process in process_names:
                    kill_cmd = "ps -fA | grep qemu-system-x86_64 | awk '{print $2}'"
                    pids_list = kill_cmd.replace("\n", ",").split(",")
                    for i in pids_list:
                        kill_cmd = f"kill -9 {i}"
                        kill_process = subprocess.Popen(
                            [kill_cmd],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                        )
                        kill_process.wait()

                    kill_cmd = f"kill -9 $(pgrep -f {process})"
                    kill_process = subprocess.Popen(
                        [kill_cmd],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                    )
                    kill_process.wait()

                    kill_cmd = f'pkill -f "{process}"'
                    kill_process = subprocess.Popen(
                        [kill_cmd],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                    )
                    kill_process.wait()

                # Logging process
                log_activity(
                    self.user_avd.id,
                    action_type="KillEmulator",
                    msg=f"Killed all available emulators for {self.user_avd.name}",
                    error=None,
                )

                # remove lock files to reinitiate device
                rm_cmd = f"rm {settings.AVD_DIR_PATH}/{self.emulator_name}.avd/*.lock"
                rm_process = subprocess.Popen(
                    [rm_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                )
                rm_process.wait()

                relaunch_adb = "adb devices"
                adb_process = subprocess.Popen(
                    [relaunch_adb],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                )
                adb_process.wait()

            time.sleep(2)

        except Exception as e:
            print("Error in killing bot instances", e)


    def check_for_conditions(self, driver):
        # Check if account is suspended
        alert_ele_id = driver.find_elements_by_id('android:id/alertTitle')
        alert_message = driver.find_elements_by_id('android:id/message')
        alert_element = alert_ele_id or alert_message

        if alert_element:
            if 'suspended' in alert_element[0].text.lower():
                dismiss_btn_id = driver.find_elements_by_id('android:id/button2')
                dismiss_btn_xpath = driver.find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[1]')
                dismiss_btn = dismiss_btn_xpath or dismiss_btn_id
                if dismiss_btn:
                    dismiss_btn[0].click()
                    time.sleep(4)

        """
        Identify and verify verification: check which verification asked by twitter and
        verify.
        """
        continue_btn = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Continue to Twitter")'
        )
        continue_btn[0].click() if continue_btn else None

        code_element = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("Didn\'t receive a code?")'
        )
        code_element[0].click() if code_element else None

        phone_verification_text = (
            "Verify your identity by entering the phone number associated "
            "with your Twitter account."
        )
        elements = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("{phone_verification_text}")'
        )

        are_you_robot = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Are you a robot?")'
        )

        if len(elements):
            self.verify_phone_number()

        captcha_verificatoin_text = "Pass a Google reCAPTCHA challenge"
        phone_verification_text = "Verify your phone number"
        captcha_element = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("{captcha_verificatoin_text}")'
        )
        captcha_element_2 = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("To get back to the Tweets, select Start to verify you\'re really human.")'
        )
        phone_element = self.app_driver.find_elements_by_android_uiautomator(
            f'new UiSelector().text("{phone_verification_text}")'
        )
        if captcha_element and phone_element:
            log_activity(
                self.user_avd.id,
                action_type="CaptchaAndPhoneVerification",
                msg=f"Twitter Asked for captcha and phone verification for {self.user_avd.name}",
                error=None,
            )
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(5)
            self.bypass_captcha()
            log_activity(
                self.user_avd.id,
                action_type="CaptchaVerification",
                msg=f"Google Capcha verified successfully for {self.user_avd.name}",
                error=None,
            )
            # Phone verification
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(3)
            send_code_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Send code")')
            send_code_btn[0].click() if send_code_btn else None
            get_twitter_number(mobile=self.phone)
            code = get_twitter_sms(phone_number=self.phone)
            confirmation_input = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Enter confirmation code")'
            )
            confirmation_input[0].clear() if confirmation_input else None
            confirmation_input[0].send_keys(code) if confirmation_input else None
            next_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Next")')
            next_btn[0].click() if next_btn else None
            continue_btn = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Continue to Twitter")'
            )
            continue_btn[0].click() if continue_btn else None
            log_activity(
                self.user_avd.id,
                action_type="PhoneVerification",
                msg=f"Phone number verified successfully for {self.user_avd.name}",
                error=None,
            )
        elif captcha_element or captcha_element_2 or are_you_robot:
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(5)
            self.bypass_captcha()
            log_activity(
                self.user_avd.id,
                action_type="OnlyCaptchaVerification",
                msg=f"Google captcha verified successfully for {self.user_avd.name}",
                error=None,
            )
        elif phone_element or code_element:
            start_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Start")')
            start_btn[0].click() if start_btn else None
            time.sleep(3)
            send_code_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Send code")')
            send_code_btn[0].click() if send_code_btn else None
            get_twitter_number(mobile=self.phone)
            code = get_twitter_sms(phone_number=self.phone)
            confirmation_input = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Enter confirmation code")'
            )
            confirmation_input[0].clear() if confirmation_input else None
            confirmation_input[0].send_keys(code) if confirmation_input else None
            next_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Next")')
            next_btn[0].click() if next_btn else None
            continue_btn = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Continue to Twitter")'
            )
            continue_btn[0].click() if continue_btn else None
            log_activity(
                self.user_avd.id,
                action_type="OnlyPhoneVerification",
                msg=f"Phone number verified successfully for {self.user_avd.name}",
                error=None,
            )

    def connect_to_nord_vpn(self, fail_tried=0):
        print("Connecting to Nord VPN")
        self.check_apk_installation()
        country = self.user_avd.country
        if re.search("surfshark", str(country), re.I):
            country_code = country[:2]
            surf_shark_country = COUNTRY_CODES[country_code]
            nord_vpn_countries = difflib.get_close_matches(surf_shark_country, NordVpn.get_server_list())
            country = random.choice(nord_vpn_countries)
            self.user_avd.proxy_type = "NORD_VPN"
            self.user_avd.country = country
            self.user_avd.save()
        vpn = NordVpn(self.driver(), self.user_avd)
        try:
            if vpn.connect_to_vpn(country, fail_tried=fail_tried):
                return True
        except Exception as e:
            print(f"Error: {e}")
        fail_tried += 1
        if fail_tried <= 3:
            if self.connect_to_nord_vpn(fail_tried):
                return True
        return False
