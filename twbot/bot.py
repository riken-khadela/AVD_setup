import difflib
from pathlib import Path
from socket import timeout

from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from ppadb.client import Client as AdbClient
from selenium.common.exceptions import InvalidSessionIdException

import parallel
from conf import APPIUM_SERVER_HOST, APPIUM_SERVER_PORT
from conf import RECAPTCHA_ALL_RETRY_TIMES
from conf import TWITTER_VERSIONS
from conf import WAIT_TIME
from constants import COUNTRY_CODES
from exceptions import AccountLimitedException, AccountSuspendedException
from exceptions import CannotRegisterThisPhoneNumberException, CannotGetSms
from exceptions import CannotStartDriverException
from exceptions import PhoneRegisteredException
from twbot.actions.voice_recaptcha_solver import (
    audio_to_text,
    load_audio,
    start_recording,
    stop_recording,
)
from twbot.dialogs import AccountSuspendedDialog, AccountFollowingExceededDialog
from twbot.models import *
from twbot.utils import *
from twbot.vpn.nord_vpn import NordVpn
from utils import get_installed_packages
from utils import get_random_file_name
from utils import run_cmd
from verify import RecaptchaAndroidUI, FuncaptchaAndroidUI
from accounts_conf import GETSMSCODE_PID

timeout = 10

class TwitterBot:
    def __init__(self, emulator_name, start_appium=True, start_adb=True,
                 appium_server_port=APPIUM_SERVER_PORT, adb_console_port=None):
        self.emulator_name = emulator_name
        self.user_avd = UserAvd.objects.get(name=emulator_name)
        self.logger = LOGGER
        #  self.kill_bot_process(appium=True, emulators=True)
        self.app_driver = None
        #  self.emulator_port = None
        #  self.service = self.start_appium(port=4724) if start_appium else None
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

        self.wait_time = WAIT_TIME

        # parallel running configration
        self.appium_server_port = appium_server_port
        if not parallel.get_listening_adb_pid():
            run_cmd('adb start-server')
        parallel.start_appium(port=self.appium_server_port)
        #  parallel.start_appium_without_exit()
        if not adb_console_port:
            self.adb_console_port = str(
                parallel.get_one_available_adb_console_port())
            self.system_port = str(parallel.get_one_available_system_port(
                int(self.adb_console_port)))
        else:
            self.adb_console_port = adb_console_port
        self.system_port = str(parallel.get_one_available_system_port(
            int(self.adb_console_port)))
        self.emulator_port = self.adb_console_port
        self.parallel_opts = self.get_parallel_opts()

    @property
    def wait_obj(self):
        """Used for waiting certain element appear"""
        return WebDriverWait(self.driver(), self.wait_time)

    def get_parallel_opts(self):
        return {
            'appium:avd': self.emulator_name,
            'appium:avdArgs': ['-port', str(self.adb_console_port)] + self.get_avd_options(),
            'appium:systemPort': self.system_port,
            'appium:noReset': True,
            #  'appium:skipLogCapture': True,
        }

    def start_appium(self, port):
        # start appium server
        LOGGER.debug(f'Start appium server, port: {port}')
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

    def get_avd_options(self):
        emulator_options = [
            # Set the emulation mode for a camera facing back or front
            #  '-camera-back', 'emulated',
            #  '-camera-front', 'emulated',

            #  '-phone-number', str(self.phone) if self.phone else '0',

        ]

        if self.user_avd.timezone:
            emulator_options += ['-timezone', f"{self.user_avd.timezone}"]
        LOGGER.debug(f'Other options for emulator: {emulator_options}')
        return emulator_options

    def get_device(self):
        name = self.emulator_name

        #  LOGGER.debug(f'Start AVD: {name}')

        #  if not self.device:
        #      LOGGER.debug(f'Start AVD: ["emulator", "-avd", "{name}"] + '
        #                   f'{self.get_avd_options()}')
        #      self.device = subprocess.Popen(
        #          #  ["emulator", "-avd", f"{name}"],
        #          ["emulator", "-avd", f"{name}"] + self.get_avd_options(),
        #          stdout=subprocess.PIPE,
        #          stderr=subprocess.PIPE,
        #          universal_newlines=True,
        #      )
        #      time.sleep(5)
        #      log_activity(
        #          self.user_avd.id,
        #          action_type="StartAvd",
        #          msg=f"Started AVD for {self.user_avd.name}",
        #          error=None,
        #      )

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
        LOGGER.debug('Terminate cyberghost vpn')
        vpn = CyberGhostVpn(self.driver())
        if vpn.is_app_installed():
            vpn.terminate_app()

        self.driver().install_app('apk/cyberghost.apk')
        LOGGER.debug('Check if Reddit is installed')
        self.driver().install_app('apk/cyberghost.apk')
        if not self.driver().is_app_installed("com.reddit.frontpage"):
            LOGGER.debug('Reddit is not installed, now install it')
            self.install_apk(self.adb_console_port, "reddit")
            log_activity(
                self.user_avd.id,
                action_type="InstallReddit",
                msg=f"Reddit app installed successfully.",
                error=None,
            )

        # LOGGER.debug('Check if Reddit is installed')
        # self.driver().install_app('apk/Reddit.apk')
        # if not self.driver().is_app_installed("com.reddit.frontpage"):
        #     LOGGER.debug('Reddit is not installed, now install it')
        #     self.install_apk(self.adb_console_port, "reddit")
        #     log_activity(
        #         self.user_avd.id,
        #         action_type="InstallReddit",
        #         msg=f"Reddit app installed successfully.",
        #         error=None,
        #     )
        # if not self.driver().is_app_installed("com.surfshark.vpnclient.android"):
        #     self.install_apk(self.emulator_port, "surfshark")
        #  LOGGER.debug('Check if instagram is installed')
        #  if not self.driver().is_app_installed("com.instagram.android"):
        #      self.install_apk(self.emulator_port, "instagram")
        #      log_activity(
        #          self.user_avd.id,
        #          action_type="InstallInstagram",
        #          msg=f"Instagram app installed successfully.",
        #          error=None,
        #      )
        # if not self.driver().is_app_installed("com.github.shadowsocks"):
        #     self.install_apk(self.emulator_port, "shadowsocks")
        #     log_activity(
        #         self.user_avd.id,
        #         action_type="InstallShadowsocks",
        #         msg=f"Shadowsocks app installed successfully.",
        #         error=None,
        #     )
        LOGGER.debug('Check if nordvpn is installed')
        if self.driver().is_app_installed("com.nordvpn.android"):
            self.driver().remove_app('com.nordvpn.android')
            # self.install_apk(self.emulator_port, "nord_vpn")
            # log_activity(
            #     self.user_avd.id,
            #     action_type="NordVPN",
            #     msg=f"NordVPN app installed successfully.",
            #     error=None,
            # )

    def get_adb_device(self):
        #  LOGGER.debug('Get adb device')
        for x in range(20):
            if self.adb.devices():
                try:
                    response = self.adb.devices()[0].shell("getprop sys.boot_completed | tr -d '\r'")
                    if "1" in response:
                        self.emulator_port = self.adb.devices()[0].serial.split("-")[-1]
                        return self.adb.devices()[0]
                except Exception as e:
                    #  print(e)
                    LOGGER.error(e)
            time.sleep(x)

    def start_driver(self):
        try:
            opts = {
                "platformName": "Android",
                #  "platformVersion": "9.0",    # comment it in order to use other android version
                "automationName": "UiAutomator2",
                "noSign": True,
                "noVerify": True,
                "ignoreHiddenApiPolicyError": True,
                # "newCommandTimeout": 30,#Don't use this
                #  "systemPort": "8210",
                #  'isHeadless': True,
                # "udid": f"emulator-{self.emulator_port}",
            }

            opts.update(self.parallel_opts)

            #  LOGGER.debug('Start appium driver')
            LOGGER.debug(f'Driver capabilities: {opts}')
            LOGGER.debug(f"Driver url: http://{APPIUM_SERVER_HOST}:{self.appium_server_port}/wd/hub")

            self.app_driver = webdriver.Remote(
                f"http://{APPIUM_SERVER_HOST}:{self.appium_server_port}/wd/hub",
                desired_capabilities=opts,
                #  keep_alive=True,
            )
            self.start_driver_retires = 0
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Driver started successfully",
                error=None,
            )
        except Exception as e:
            LOGGER.warning(type(e))
            LOGGER.warning(e)

            if not parallel.get_avd_pid(name=self.emulator_name,
                                        port=self.adb_console_port):
                self.adb_console_port = str(
                    parallel.get_one_available_adb_console_port())
                adb_console_port = self.adb_console_port
            else:
                adb_console_port = str(
                    parallel.get_one_available_adb_console_port())
            self.system_port = str(parallel.get_one_available_system_port(
                int(adb_console_port)))
            self.parallel_opts = self.get_parallel_opts()
            if not parallel.get_listening_adb_pid():
                run_cmd('adb start-server')
            parallel.start_appium(port=self.appium_server_port)

            tb = traceback.format_exc()
            if self.start_driver_retires > 5:
                LOGGER.info("================ Couldn't start driverCouldn't start driver")
                log_activity(
                    self.user_avd.id,
                    action_type="ConnectAppium",
                    msg=f"Error while connecting with appium server",
                    error=tb,
                )
                raise CannotStartDriverException("Couldn't start driver")
            #  print("killed in start_driver")
            #  self.kill_bot_process(True, True)
            #  self.service = self.start_appium(port=4724)

            self.start_driver_retires += 1
            LOGGER.info(f"appium server starting retries: {self.start_driver_retires}")
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Error while connecting with appium server",
                error=f"Failed to connect with appium server retries_value: {self.start_driver_retires}",
            )
            self.driver()

    def driver(self, check_verification=True):
        #  LOGGER.debug('Get driver')
        #  assert self.get_device(), "Device Didn't launch."

        try:
            if not self.app_driver:
                self.start_driver()
            session = self.app_driver.session
        except CannotStartDriverException as e:
            raise e
        except Exception as e:
            #  tb = traceback.format_exc()
            #  log_activity(
            #      self.user_avd.id,
            #      action_type="ConnectAppium",
            #      msg=f"Connect with Appium server",
            #      error=tb,
            #  )
            LOGGER.warning(e)
            self.start_driver()

        # check and bypass google captcha
        #  random_sleep()
        self.perform_verification()
        popup = self.app_driver.find_elements_by_android_uiautomator(
            'new UiSelector().text("Wait")'
        )
        popup[0].click() if popup else None
        return self.app_driver

    @staticmethod
    def create_avd(avd_name, package=None, device=None):
        default_package = "system-images;android-28;default;x86"

        try:
            if not package:
                cmd = f'avdmanager create avd --name {avd_name} --package "{default_package}"'
                package = default_package
            else:
                cmd = f'avdmanager create avd --name {avd_name} --package "{package}"'

            if device:
                #  cmd += f" --device {device}"
                cmd += f" --device \"{device}\""

            # install package
            if package not in get_installed_packages():
                LOGGER.info(f'Install or update package: {package}')
                cmd1 = f'sdkmanager "{package}"'
                p = subprocess.Popen(cmd1, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, shell=True, text=True)
                # print live output
                while True:
                    output = p.stdout.readline()
                    if p.poll() is not None:
                        break
                    if output:
                        print(output.strip())

            LOGGER.info(f'AVD command: {cmd}')
            #  result = run_cmd(cmd)
            #  return result
            p = subprocess.Popen(
                [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
            )
            time.sleep(1)
            p.communicate(input=b"\n")
            p.wait()
            return True

        except Exception as e:
            LOGGER.error(e)
            return False

    def install_apk(self, port, app_name):
        try:
            if app_name.lower() == "reddit":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/Reddit.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallRedditApk",
                    msg=f"Installation of Reddit apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            if app_name.lower() == "instagram":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/instagram.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallInstagramApk",
                    msg=f"Installation of instagram apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            elif app_name.lower() == "twitter":
                #  cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/twitter.apk')}"
                times = 0
                retry_times = 10
                apk_path = ''
                while times < retry_times:
                    twitter_version = random.choice(TWITTER_VERSIONS)
                    apk_path = os.path.join(BASE_DIR, f'apk/twitter_{twitter_version}.apk')
                    times += 1
                    if Path(apk_path).exists():
                        break

                if apk_path == '':
                    LOGGER.critical(f'Cannot find twitter apk, please'
                                    ' configure the versions in the file conf.py')
                    # use the defaut apk
                    apk_path = os.path.join(BASE_DIR, f'apk/twitter.apk')

                # get architecture of device
                arch = self.get_arch_of_device()
                if arch:
                    cmd = f"adb -s emulator-{port} install --abi {arch} {apk_path}"
                else:
                    cmd = f"adb -s emulator-{port} install {apk_path}"
                LOGGER.debug(f'Install cmd: {cmd}')
                log_activity(
                    self.user_avd.id,
                    action_type="InstallTwitterApk",
                    msg=f"Installation of twitter apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            elif app_name.lower() == "shadowsocks":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/shadowsocks.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallShadowsockApk",
                    msg=f"Installation of shadowsocks apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()

            elif app_name.lower() == "nord_vpn":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/nord_vpn.apk')}"
                LOGGER.debug(f'Install cmd: {cmd}')
                log_activity(
                    self.user_avd.id,
                    action_type="InstallNordVPNApk",
                    msg=f"Installation of NordVPN apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            else:
                return False

            return True
        except Exception as e:
            print(e)
            return False

    def run_script(self, *args, **options):
        self.perform_login()
        print("login process completed")
        #  self.service.stop()
        #  print("stopped appium server")
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
                    action_type="ConnectShadowsockError",
                    msg=f"Failed to connect shadowsocks",
                    error="VPN STATUS: Invalid Settings.",
                )

        print("VPN STATUS: Network Issue.")
        log_activity(
            self.user_avd.id,
            action_type="ConnectShadowsockError",
            msg=f"Failed to connect shadowsocks",
            error="VPN STATUS: Network Issue.",
        )
        fail_tried += 1
        if fail_tried <= 3:
            socket = random.choice(self.get_default_shadowsocks())
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
        LOGGER.info('Login twitter')
        #  if self.service.is_running and self.service.is_listening:

        if self.driver().current_activity == ".picker.PickActivity":
            LOGGER.debug('Press back key')
            self.driver().press_keycode(4)  # press back key

        # goto home page
        self.driver().press_keycode(3)
        time.sleep(3)

        # get details from twitter account
        twitter_account = self.user_avd.twitter_account
        username = twitter_account.phone if not twitter_account.screen_name else twitter_account.screen_name
        password = twitter_account.password

        # launch target app ( twitter )
        start_app(self.driver, "twitter")

        if self.check_suspended_dialog():
            raise AccountSuspendedException

        LOGGER.debug(f'current_activity: {self.driver().current_activity}')
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
            #  time.sleep(2)
            random_sleep()
            self.driver().find_element_by_id("com.twitter.android:id/login_identifier").send_keys(username)
            #  time.sleep(2)
            random_sleep()
            self.driver().find_element_by_id(
                "com.twitter.android:id/login_password"
            ).send_keys(password)
            #  time.sleep(2)
            random_sleep()
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
        #  else:
        #      log_activity(
        #          self.user_avd.id,
        #          action_type="LoginAccount",
        #          msg=f"Skipped login appium service not running",
        #          error=None
        #      )

    def create_account_twitter(self, full_name, password, phone, pid=GETSMSCODE_PID):
        """
        create_account_twitter: creates twitter account with given user details.

        args:
        full_name: user full name
        password: user password
        phone: united state phone number
        """
        LOGGER.debug(f'Create twitter account: (name: {full_name},'
                     f' password: {password}, phone: {phone}')
        self.phone = phone
        start_app(self.driver, "twitter")

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
            create_account_btn[0].click()

        random_sleep()

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

        birthday_picker_id = 'android:id/pickers'
        birthday_picker = self.driver().find_element_by_id(birthday_picker_id)
        LOGGER.debug(f'birthday_picker: {birthday_picker}')
        random_sleep()

        month_picker_relative_xpath = 'android.widget.NumberPicker[1]'
        day_picker_relative_xpath = 'android.widget.NumberPicker[2]'
        year_picker_relative_xpath = 'android.widget.NumberPicker[3]'

        middle_month_picker_relative_xpath = '//android.widget.NumberPicker[1]/android.widget.EditText'
        middle_day_picker_relative_xpath = '//android.widget.NumberPicker[2]/android.widget.EditText'
        middle_year_picker_relative_xpath = '//android.widget.NumberPicker[3]/android.widget.EditText'

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
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        LOGGER.debug('swipe month')
        for i in range(random.randint(3, 12)):
            self.driver().swipe(
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
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        LOGGER.debug('swipe day')
        for i in range(random.randint(1, 30)):
            self.driver().swipe(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                duration=random.randrange(200, 350),
            )
        start_x = middle_year_rect['x'] + middle_year_rect['width'] / 2
        start_y = middle_year_rect['y'] + middle_year_rect['height'] / 2
        end_x = start_x
        end_y = start_y + middle_year_rect['height']
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        LOGGER.debug('swipe year')
        for i in range(random.randint(17, 35)):
            self.driver().swipe(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                duration=random.randrange(200, 550),
            )

        #  for i in range(random.randint(3, 7)):
        #      self.driver().swipe(
        #          start_x=80,
        #          start_y=500,
        #          end_x=80,
        #          end_y=575,
        #          duration=random.randrange(200, 250),
        #      )
        #  for i in range(random.randint(5, 15)):
        #      self.driver().swipe(
        #          start_x=160,
        #          start_y=500,
        #          end_x=155,
        #          end_y=575,
        #          duration=random.randrange(100, 150),
        #      )
        #  for i in range(random.randint(17, 19)):
        #      self.driver().swipe(
        #          start_x=240,
        #          start_y=500,
        #          end_x=240,
        #          end_y=575,
        #          duration=random.randrange(200, 550),
        #      )
        #
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
        for i in range(10):
            if i >= 9:
                raise PhoneRegisteredException
            # check if the phone number is registered
            phone_field_id = self.driver().find_elements_by_id(
                "com.twitter.android:id/phone_or_email_field"
            )
            phone_field_xpath = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
                ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
                "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[2]"
            )
            phone_field = phone_field_id or phone_field_xpath
            if phone_field:
                ban_twitter_number(phone.replace("+", ""), pid=pid)
                LOGGER.debug('The phone number is already registered,'
                             ' now change the number')
                time.sleep(10)
                phone = get_twitter_number()
                if "unavailable" in phone:
                    LOGGER.debug('Phone number not available retry in 3s')
                    time.sleep(3)
                    continue
                LOGGER.info(f'''
                            ********************
                            Name: {full_name}
                            Password: {password}
                            Phone: {phone}
                            ********************
                            ''')
                phone_field[0].click()
                phone_field[0].clear()
                phone_field[0].send_keys("+" + phone)
                press_enter(self.driver)
                time.sleep(3)
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
            else:
                break

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
        # fix a bug: the button 'Sign up' doesn't appear
        for c in range(3):
            signup_btn_id = self.driver().find_elements_by_id(
                "com.twitter.android:id/cta_button"
            )
            signup_btn_xpath = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
                ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
                "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.Button"
            )
            signup_btn = signup_btn_id or signup_btn_xpath
            if signup_btn:
                break
            else:
                LOGGER.debug('Button Sign up disappears, now swipe up')
                swipe_up(self.driver)
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
            ban_twitter_number(phone.replace("+", ""), pid=pid)
            LOGGER.error("*** Failed to get verification field ***")
            #  return False
            raise CannotRegisterThisPhoneNumberException

        LOGGER.debug(f'pid: {pid}')
        otp = get_twitter_sms(phone.replace("+", ""), pid=pid,
                purpose=Sms.CREATE_ACCOUNT)
        if not otp:
            random_sleep(20, 30)
            LOGGER.debug('Get SMS again')
            otp = get_twitter_sms(phone.replace("+", ""), pid=pid,
                    purpose=Sms.CREATE_ACCOUNT)
            if not otp:
                ban_twitter_number(phone.replace("+", ""), pid=pid)
                LOGGER.error("*** Failed to get otp ***")
                raise CannotGetSms
            #  return False

        try:
            verify_code_field[0].send_keys(otp)
            # self.driver().implicitly_wait(10)
            time.sleep(4)
        except Exception as e:
            LOGGER.error(e)

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
        return username, phone

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
                        LOGGER.debug("Pressed play audio button")
                    except:
                        self.app_driver.tap(
                            [(random.randrange(40, 280), random.randrange(127, 169))]
                        )
                    time.sleep(8)

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

    def profile_setup_or_update(self, edit=False):
        LOGGER.info(f'Edit or update profile, is edit: {edit}')
        twitter_account = self.user_avd.twitter_account
        full_name = twitter_account.full_name
        bio = twitter_account.bio
        profile_image_url = twitter_account.profile_image
        banner_image_url = twitter_account.banner_image
        location = twitter_account.location

        # download profile image
        file_name = get_random_file_name()
        download_image(url=profile_image_url, image_name=f"{file_name}.jpg")
        file_path = os.path.join(BASE_DIR, f"images/{file_name}.jpg")

        # delete all files in download folder
        delete_download_files(self.adb_console_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.adb_console_port)

        ok_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("OK")')
        ok_btn[0].click() if ok_btn else None

        # go to edit profile
        navigation_btn_id = self.driver().find_elements_by_id("Show navigation drawer")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show navigation drawer"]'
        )
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        LOGGER.debug(f'Click navigation_btn')
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
        LOGGER.debug('Click profile_btn')
        for x in range(5):
            print(f"*** checking profile page load with wait: {x}sec")
            if self.driver().current_activity == "com.twitter.app.profiles.ProfileActivity":
                break
            else:
                time.sleep(x)
        time.sleep(2)
        edit_profile_btn = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("EDIT PROFILE")'
        )
        if edit_profile_btn:
            account = TwitterAccount.objects.get(id=self.user_avd.twitter_account.id)
            account.profile_updated = True
            account.save()
            self.update_profile(self.user_avd.twitter_account) if edit else print(
                "Profile already updated so skipping")
        else:
            self.setup_account()
        time.sleep(2)

    def setup_account(self):
        LOGGER.info('Setup profile')
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
        LOGGER.debug(f'click edit_profile_btn')
        edit_profile_btn[0].click()
        time.sleep(5)

        # download profile image
        file_name = get_random_file_name()
        download_image(url=profile_image_url, image_name=f"{file_name}.jpg")
        file_path = os.path.join(BASE_DIR, f"images/{file_name}.jpg")

        # delete all files in download folder
        delete_download_files(self.adb_console_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.adb_console_port)

        upload_image = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Upload")')
        LOGGER.debug(f'click upload_image')
        upload_image[0].click() if upload_image else None

        choose_photo = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Choose existing photo")')
        LOGGER.debug(f'click choose_photo: {choose_photo}')
        choose_photo[0].click() if upload_image else None

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        LOGGER.debug(f'click allow: {allow_btn}')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        navigation_btn_id = self.driver().find_elements_by_accessibility_id("Show roots")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]')
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        LOGGER.debug(f'click navigation_btn: {navigation_btn}')
        navigation_btn[0].click() if navigation_btn else None
        time.sleep(5)

        download_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Downloads")')

        if download_btn:
            LOGGER.debug(f'click download_btn: {download_btn}')
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
        image_id = self.driver().find_elements_by_id(
            'com.android.documentsui:id/icon_thumb')
        image = image_xpath1 or image_xpath2 or image_id
        LOGGER.debug(f'click image: {image}')
        image[0].click() if image else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        LOGGER.debug(f'click apply_btn: {apply_btn}')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        LOGGER.debug(f'click allow_btn: {allow_btn}')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        LOGGER.debug(f'click apply_btn: {apply_btn}')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn1 = self.driver().find_elements_by_id('com.twitter.android:id/cta_button')
        next_btn = next_btn or next_btn1
        LOGGER.debug(f'click next_btn: {next_btn}')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        # download profile image
        file_name = get_random_file_name()
        download_image(url=banner_image_url, image_name=f"{file_name}.jpg")
        file_path = os.path.join(BASE_DIR, f"images/{file_name}.jpg")

        # delete all files in download folder
        delete_download_files(self.adb_console_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.adb_console_port)

        upload_image = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Upload")')
        LOGGER.debug(f'click upload_image')
        upload_image[0].click() if upload_image else None

        choose_photo = self.driver().find_elements_by_android_uiautomator(
            'new UiSelector().text("Choose existing photo")')
        LOGGER.debug(f'click choose_photo: {choose_photo}')
        choose_photo[0].click() if choose_photo else None

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        LOGGER.debug(f'click allow_btn: {allow_btn}')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        navigation_btn_id = self.driver().find_elements_by_accessibility_id("Show roots")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]')
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        LOGGER.debug(f'click navigation_btn: {navigation_btn}')
        navigation_btn[0].click() if navigation_btn else None
        time.sleep(5)

        download_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Downloads")')

        if download_btn:
            LOGGER.debug(f'click download_btn: {download_btn}')
            download_btn[-1].click()
            #  if len(download_btn) == 2:
            #      download_btn[1].click()
            #  else:
            #      download_btn[0].click()

        time.sleep(5)

        # Select Image
        image_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout ")
        image_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1] ")
        image_id = self.driver().find_elements_by_id(
            'com.android.documentsui:id/icon_thumb')
        image = image_xpath1 or image_xpath2 or image_id
        LOGGER.debug(f'click image: {image}')
        image[0].click() if image else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        LOGGER.debug(f'click apply_btn: {apply_btn}')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        LOGGER.debug(f'click allow_btn: {allow_btn}')
        allow_btn[0].click() if allow_btn else None
        time.sleep(5)

        apply_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Apply")')
        LOGGER.debug(f'click apply_btn: {apply_btn}')
        apply_btn[0].click() if apply_btn else None
        time.sleep(5)

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn1 = self.driver().find_elements_by_id('com.twitter.android:id/cta_button')
        next_btn = next_btn or next_btn1
        LOGGER.debug(f'click next_btn: {next_btn}')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        # if bio is blank, click the button 'skip'
        if not bio:
            skip_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Skip for now")')
            LOGGER.debug(f'click skip_btn: {skip_btn}')
            skip_btn[0].click() if skip_btn else None
            time.sleep(5)
        else:
            edit_btn = self.driver().find_elements_by_class_name('android.widget.EditText')
            LOGGER.debug(f'click edit_btn: {edit_btn}')
            edit_btn[0].click() if edit_btn else None

            edit_btn = self.driver().find_elements_by_class_name('android.widget.EditText')
            LOGGER.debug(f'click edit_btn: {edit_btn}')
            edit_btn[0].send_keys(bio) if edit_btn else None

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn1 = self.driver().find_elements_by_id('com.twitter.android:id/cta_button')
        next_btn = next_btn or next_btn1
        LOGGER.debug(f'click next_btn: {next_btn}')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        next_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NEXT")')
        next_btn1 = self.driver().find_elements_by_id('com.twitter.android:id/cta_button')
        next_btn = next_btn or next_btn1
        LOGGER.debug(f'click next_btn: {next_btn}')
        next_btn[0].click() if next_btn else None
        time.sleep(5)

        skip_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Skip for now")')
        LOGGER.debug(f'click skip_btn: {skip_btn}')
        skip_btn[0].click() if skip_btn else None
        time.sleep(5)

        see_profile = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("SEE PROFILE")')

        LOGGER.debug(f'click see_profile')
        see_profile[0].click() if see_profile else None
        if see_profile:
            account = TwitterAccount.objects.get(id=self.user_avd.twitter_account.id)
            account.profile_updated = True
            account.save()
        time.sleep(5)

    def update_profile(self, twitter_account):
        full_name = twitter_account.full_name
        bio = twitter_account.bio
        profile_image_url = twitter_account.profile_image
        banner_image_url = twitter_account.banner_image
        location = twitter_account.location

        LOGGER.info('Update profile for user {fullname}')

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
        LOGGER.debug(f'click edit_profile_btn: {edit_profile_btn[0]}')
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

        # update bio
        if bio:
            bio_field_id = self.driver().find_elements_by_id("com.twitter.android:id/edit_bio")
            bio_field_xpath = self.driver().find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
                ".widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView"
                "/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.EditText[2] "
            )
            bio_field = bio_field_id or bio_field_xpath
            bio_field[0].clear()
            LOGGER.debug(f'Update bio to: {bio}')
            bio_field[0].send_keys(bio)
            time.sleep(2)

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
        LOGGER.debug(f'Click button set_image: {set_image[0]}')
        set_image[0].click()
        time.sleep(2)

        continue_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("CONTINUE")')
        LOGGER.debug(f'click continue')
        continue_btn[0].click() if continue_btn else None

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        LOGGER.debug(f'click allow')
        allow_btn[0].click() if allow_btn else None

        choose_existing_photo = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.LinearLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.TextView[2] "
        )
        LOGGER.debug(f'click choose_existing_photo: {choose_existing_photo[0]}')
        choose_existing_photo[0].click()
        time.sleep(2)

        allow_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("ALLOW")')
        LOGGER.debug(f'click allow: {allow_btn}')
        allow_btn[0].click() if allow_btn else None

        navigation_btn_id = self.driver().find_elements_by_accessibility_id("Show roots")
        navigation_btn_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Show roots"]'
        )
        navigation_btn = navigation_btn_id or navigation_btn_xpath
        LOGGER.debug(f'click navigation_btn: {navigation_btn[0]}')
        navigation_btn[0].click()
        time.sleep(2)

        download_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("Downloads")')

        LOGGER.debug(f'click download_btn')
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
            continue_btn_id1 = self.driver().find_elements_by_id(
                "com.twitter.android:id/button_positive"
            )
            continue_btn_xpath = self.driver().find_elements_by_xpath(
                '//android.view.ViewGroup[@content-desc="To attach media, we need access to your gallery,'
                '"]/android.widget.Button '
            )
            continue_btn = continue_btn_id or continue_btn_xpath or continue_btn_id1
            LOGGER.debug(f'click continue_btn: {continue_btn}')
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
            allow_btn_id1 = self.driver().find_elements_by_id(
                'com.android.permissioncontroller:id/permission_allow_button')
            allow_btn = allow_btn_id or allow_btn_xpath or allow_btn_id1
            if allow_btn:
                LOGGER.debug(f'click allow_btn: {allow_btn}')
                allow_btn[0].click()
                time.sleep(2)

        # Select Image
        image_xpath1 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout ")
        image_xpath2 = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1] ")
        image_id = self.driver().find_elements_by_id(
            'com.android.documentsui:id/icon_thumb')
        image = image_xpath1 or image_xpath2 or image_id
        LOGGER.debug(f'click image: {image}')
        image[0].click()
        time.sleep(2)

        done_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/done")
        done_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout"
            "/android.widget.FrameLayout[2]/android.widget.TextView "
        )
        done_btn = done_btn_id or done_btn_xpath
        LOGGER.debug(f'click done_btn')
        done_btn[0].click() if done_btn else None
        time.sleep(2)

        # download profile image
        file_name = get_random_file_name()
        download_image(url=banner_image_url, image_name=f"{file_name}.jpg")
        file_path = os.path.join(BASE_DIR, f"images/{file_name}.jpg")

        # delete all files in download folder
        delete_download_files(self.adb_console_port)

        # push profile image to the download folder
        push_image_to_device(file_path=file_path, port=self.adb_console_port)

        # set banner
        banner_id = self.driver().find_elements_by_accessibility_id(
            "Overlay for avatar"
        )
        banner_xpath = self.driver().find_elements_by_xpath(
            '//android.widget.ImageView[@content-desc="Overlay for avatar"]'
        )
        banner = banner_id or banner_xpath
        LOGGER.debug(f'click banner')
        banner[0].click()
        time.sleep(2)

        # choose existing photo
        existing_photo = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.LinearLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.TextView[2] "
        )
        LOGGER.debug(f'click existing_photo')
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
        image_id = self.driver().find_elements_by_id(
            'com.android.documentsui:id/icon_thumb')
        image = image_xpath1 or image_xpath2 or image_id
        LOGGER.debug(f'click image: {image}')
        image[0].click() if image else None
        time.sleep(2)

        done_btn_id = self.driver().find_elements_by_id("com.twitter.android:id/done")
        done_btn_xpath = self.driver().find_elements_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
            ".widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout"
            "/android.widget.FrameLayout[2]/android.widget.TextView "
        )
        done_btn = done_btn_id or done_btn_xpath
        LOGGER.debug(f'click download_btn')
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
        LOGGER.debug(f'click save_btn')
        save_btn[0].click()
        time.sleep(2)

        for x in range(5):
            print(f"*** checking profile page load with wait: {x}sec")
            if self.driver().current_activity == "com.twitter.app.profiles.ProfileActivity":
                break
            else:
                time.sleep(x)

        not_now_btn = self.driver().find_elements_by_android_uiautomator('new UiSelector().text("NOT NOW")')
        LOGGER.debug(f'click not_now_btn')
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
        #  if self.service.is_running:
        #      self.service.stop()
        #      print("*** Stopped appium server ***")
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

    def perform_verification(self, pid=GETSMSCODE_PID):
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

        # resolve reCAPTCHA
        recaptcha = RecaptchaAndroidUI(self.app_driver)
        if recaptcha.is_captcha_first_page():
            LOGGER.info('Resovling reCAPTCHA')
            if recaptcha.resolve_all_with_coordinates_api(
                    all_resolve_retry_times=RECAPTCHA_ALL_RETRY_TIMES):
                LOGGER.info('reCAPTCHA is resolved')
            else:
                LOGGER.info('reCAPTCHA cannot be resolved')

        # resolve FunCaptcha
        funcaptcha = FuncaptchaAndroidUI(self.app_driver)
        if funcaptcha.is_captcha_first_page():
            LOGGER.info('Resovling FunCaptcha')
            if funcaptcha.resolve_all_with_coordinates_api(
                    all_resolve_retry_times=RECAPTCHA_ALL_RETRY_TIMES):
                LOGGER.info('FunCaptcha is resolved')
            else:
                LOGGER.info('FunCaptcha cannot be resolved')

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
            code = get_twitter_sms(phone_number=self.phone, pid=pid,
                    purpose=Sms.VERIFY_ACCOUNT)
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
            LOGGER.debug('click button "send code"')
            send_code_btn[0].click() if send_code_btn else None
            get_twitter_number(mobile=self.phone)
            code = get_twitter_sms(phone_number=self.phone, pid=pid,
                    purpose=Sms.VERIFY_ACCOUNT)
            confirmation_input = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Enter confirmation code")'
            )
            LOGGER.debug(f'confirmation_input: {confirmation_input}')
            confirmation_input1 = self.app_driver.find_elements_by_xpath(
                '//android.widget.FrameLayout/android.widget.LinearLayout/'
                'android.widget.FrameLayout/android.webkit.WebView/'
                'android.webkit.WebView/android.view.View[4]/android.widget.EditText'
            )
            LOGGER.debug(f'confirmation_input1: {confirmation_input1}')
            confirmation_input2 = self.app_driver.find_elements_by_id(
                'code'
            )
            LOGGER.debug(f'confirmation_input2: {confirmation_input2}')
            confirmation_input = confirmation_input or confirmation_input1 or confirmation_input2
            LOGGER.debug(f'Last confirmation_input: {confirmation_input}')
            confirmation_input[0].clear() if confirmation_input else None
            confirmation_input[0].send_keys(code) if confirmation_input else None
            next_btn = self.app_driver.find_elements_by_android_uiautomator('new UiSelector().text("Next")')
            next_btn[0].click() if next_btn else None
            random_sleep()
            continue_btn = self.app_driver.find_elements_by_android_uiautomator(
                'new UiSelector().text("Continue to Twitter")'
            )
            continue_btn[0].click() if continue_btn else None
            random_sleep()
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
        LOGGER.debug(f'Start to kill the AVD: {self.emulator_name}')
        if self.app_driver:
            LOGGER.info(f'Stop the driver session')
            try:
                self.app_driver.quit()
            except InvalidSessionIdException as e:
                LOGGER.info(e)

        name = self.emulator_name
        port = self.adb_console_port
        parallel.stop_avd(name=name, port=port)
        #  LOGGER.debug(f'Start to kill bot processes')
        #  LOGGER.debug(f'appium: {appium}, emulators: {emulators}')

        #  run_verbose = True
        #  run_verbose = False
        #  try:
        #      # Kill all running appium instances
        #      if appium:
        #          kill_cmd = "kill -9 $(pgrep -f appium)"
        #          run_cmd(kill_cmd, verbose=run_verbose)
        #
        #          kill_cmd = "fuser -k -n tcp 4724"
        #          run_cmd(kill_cmd, verbose=run_verbose)
        #
        #          log_activity(
        #              self.user_avd.id,
        #              action_type="KillAppiumServer",
        #              msg=f"Killed appium server for {self.user_avd.name}",
        #              error=None,
        #          )
        #
        #      # Kill All emulators
        #      if emulators:
        #          self.device = None
        #          process_names = [
        #              "qemu-system-x86_64",
        #              "qemu-system-x86",
        #              "emulator64-crash-service",
        #              "adb",
        #          ]
        #          for process in process_names:
        #              kill_cmd = f"pkill --signal TERM {process}"
        #              run_cmd(kill_cmd, verbose=run_verbose)
        #              pkill_process_after_waiting(process, success_code=1,
        #                                          verbose=run_verbose)
        #
        #          # Logging process
        #          log_activity(
        #              self.user_avd.id,
        #              action_type="KillEmulator",
        #              msg=f"Killed all available emulators for {self.user_avd.name}",
        #              error=None,
        #          )
        #
        #          # remove lock files to reinitiate device
        #          rm_cmd = f"rm {settings.AVD_DIR_PATH}/{self.emulator_name}.avd/*.lock"
        #          run_cmd(kill_cmd, verbose=run_verbose)
        #
        #          )
        #
        #          # remove lock files to reinitiate device
        #          rm_cmd = f"rm {settings.AVD_DIR_PATH}/{self.emulator_name}.avd/*.lock"
        #          run_cmd(kill_cmd, verbose=run_verbose)
        #
        #      #  time.sleep(2)
        #
        #  except Exception as e:
        #      print("Error in killing bot instances", e)
        #      #  time.sleep(2)
        #
        #  except Exception as e:
        #      print("Error in killing bot instances", e)

    def connect_to_vpn(self, fail_tried=0, vpn_type='cyberghostvpn',
                       country='', city=""):
        self.check_apk_installation()
        if not country:
            country = self.user_avd.country
        if re.search("surfshark", str(country), re.I):
            country_code = country[:2]
            surf_shark_country = COUNTRY_CODES[country_code]
            nord_vpn_countries = difflib.get_close_matches(surf_shark_country, NordVpn.get_server_list())
            country = random.choice(nord_vpn_countries)
            self.user_avd.proxy_type = "CYBERGHOST"
            self.user_avd.country = country
            self.user_avd.save()

        if vpn_type == 'cyberghostvpn':
            ghost_vpn_countries = difflib.get_close_matches(country, CyberGhostVpn.get_server_list())
            country = random.choice(ghost_vpn_countries)
            if not country:
                country = "United States"
            self.user_avd.proxy_type = "CYBERGHOST"
            self.user_avd.country = country
            self.user_avd.save()
            LOGGER.info('Connect to CyberGhost VPN')
            vpn = CyberGhostVpn(self.driver())
            reconnect = True
            #  country = 'United States' if not vpn_country else vpn_country
            return vpn.start_ui(reconnect=reconnect, country=country, city=city)
        else:
            LOGGER.debug('Connect to Nord VPN')
            vpn = NordVpn(self.driver(), self.user_avd)
            try:
                if vpn.connect_to_vpn(country, fail_tried=fail_tried):
                    return True
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                print(f"Error: {e}")
            fail_tried += 1
            if fail_tried <= 3:
                if self.connect_to_vpn(fail_tried):
                    return True
            return False

    def get_arch_of_device(self):
        LOGGER.debug('Get the architecture of the current device')
        device = self.adb.device(f'emulator-{self.adb_console_port}')
        if device:
            arch = device.shell('getprop ro.product.cpu.abi').strip()
            LOGGER.debug(f'Architecture of current device: {arch}')
            return arch

    def check_suspended_dialog(self):
        suspended_dialog = AccountSuspendedDialog(self.app_driver,
                                                  logger=LOGGER)
        if suspended_dialog.exists():
            # change the status of the account
            account = self.user_avd.twitter_account
            account.status = 'SUSPENDED'
            account.save()
            LOGGER.info(f'Changed the status of "{account.screen_name}"'
                        ' to SUSPENDED')
            suspended_dialog.click_dismiss_button()
            return True

    def check_limited_dialog(self):
        limited_dialog = AccountFollowingExceededDialog(self.app_driver,
                                                        logger=LOGGER)
        if limited_dialog.exists():
            # change the status of the account
            account = self.user_avd.twitter_account
            account.status = 'LIMITED'
            account.save()
            LOGGER.info(f'Changed the status of "{account.screen_name}"'
                        ' to LIMITED')
            limited_dialog.click_dismiss_button()
            return True

    def get_arch_of_device(self):
        LOGGER.debug('Get the architecture of the current device')
        device = self.adb.device(f'emulator-{self.adb_console_port}')
        if device:
            arch = device.shell('getprop ro.product.cpu.abi').strip()
            LOGGER.debug(f'Architecture of current device: {arch}')
            return arch

    def check_suspended_dialog(self):
        suspended_dialog = AccountSuspendedDialog(self.app_driver,
                                                  logger=LOGGER)
        if suspended_dialog.exists():
            # change the status of the account
            account = self.user_avd.twitter_account
            account.status = 'SUSPENDED'
            account.save()
            LOGGER.info(f'Changed the status of "{account.screen_name}"'
                        ' to SUSPENDED')
            suspended_dialog.click_dismiss_button()
            return True

    def check_limited_dialog(self):
        limited_dialog = AccountFollowingExceededDialog(self.app_driver,
                                                        logger=LOGGER)
        if limited_dialog.exists():
            # change the status of the account
            account = self.user_avd.twitter_account
            account.status = 'LIMITED'
            account.save()
            LOGGER.info(f'Changed the status of "{account.screen_name}"'
                        ' to LIMITED')
            limited_dialog.click_dismiss_button()
            return True

    def check_abnormal_dialogs(self):
        if self.check_limited_dialog():
            return AccountLimitedException
        if self.check_suspended_dialog():
            return AccountSuspendedException

    @staticmethod
    def get_number_of_avds_running():
        out = subprocess.check_output(['adb', 'devices'])
        return len(re.findall("emulator", out, re.I))


    def find_element(self, element, locator, locator_type=By.XPATH,
            page=None, timeout=10,
            condition_func=EC.presence_of_element_located,
            condition_other_args=tuple()):
        """Find an element, then return it or None.
        If timeout is less than or requal zero, then just find.
        If it is more than zero, then wait for the element present.
        """
        time.sleep(3)
        try:
            if timeout > 0:
                wait_obj = WebDriverWait(self.app_driver, timeout)
                ele = wait_obj.until(
                        condition_func((locator_type, locator),
                            *condition_other_args))
            else:
                self.logger.debug(f'Timeout is less or equal zero: {timeout}')
                ele = self.app_driver.find_element(by=locator_type,
                        value=locator)
            if page:
                self.logger.debug(
                        f'Found the element "{element}" in the page "{page}"')
            else:
                self.logger.debug(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                self.logger.debug(f'Cannot find the element "{element}"'
                        f' in the page "{page}"')
            else:
                self.logger.debug(f'Cannot find the element: {element}')


    
    def click_element(self, element, locator, locator_type=By.XPATH,
            timeout=timeout,page=None):
        time.sleep(3)
        
        """Find an element, then click and return it, or return None"""
        ele = self.find_element(element, locator, locator_type, timeout=timeout,page=page)
        if ele:
            ele.click()
            LOGGER.debug(f'Clicked the element: {element}')
            return ele

    def input_text(self, text, element, locator, locator_type=By.XPATH,
            timeout=timeout, hide_keyboard=True,page=None):
        time.sleep(3)
        
        """Find an element, then input text and return it, or return None"""
        try:
            if hide_keyboard :
                self.logger.debug(f'Hide keyboard')
                try:self.app_driver.hide_keyboard()
                except:None

            ele = self.find_element(element, locator, locator_type=locator_type,
                    timeout=timeout,page=page)
            if ele:
                ele.clear()
                ele.send_keys(text)
                self.logger.debug(f'Inputed "{text}" for the element: {element}')
                return ele
        except Exception as e :
            self.logger.info(f'Got an error in input text :{element} {e}')

    def create_account(self):
        # self.driver.activate_app('com.reddit.frontpage')
        self.app_driver.start_activity('com.reddit.frontpage','com.reddit.frontpage.MainActivity')
        sign_up_id = 'com.reddit.frontpage:id/signup_button'
        self.click_element('Sign up btn',sign_up_id,By.ID)
        choose_acc_ele = self.find_element('Choose an account','android:id/title',By.ID,timeout=4)
        if choose_acc_ele:
            all_option_account = self.app_driver.find_elements(By.XPATH,'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.ListView/*')
            for i in all_option_account:
                print(i.get_attribute('text'))
                if i.get_attribute('text') == 'Add account':
                    i.click()
            self.click_element('Ok btn','android:id/button2',By.ID)
        profile_name = ''
        
                    

        get_email = requests.get('http://localhost:5000/get/').text
        time.sleep(3)
        get_email =  json.loads(get_email)
        new_email = str(get_email['email'])
        profile_name = str(get_email['profile'])
        print(new_email,'------------------')
        time.sleep(3)

        username_row = new_email.split('@')
        username = username_row[0]+'_'+username_row[-1].split('.')[0]
        password = username_row[0]+username_row[-1].split('.')[0]
        self.input_text(new_email,'email','com.reddit.frontpage:id/email',By.ID)
        self.input_text(username,'username','com.reddit.frontpage:id/username',By.ID)
        self.input_text(password,'password','com.reddit.frontpage:id/password',By.ID)
        self.click_element('create account','com.reddit.frontpage:id/confirm',By.ID)

        verify_email = requests.get(f'http://localhost:5000/verify/{profile_name}').text
        verify_email = json.loads(verify_email)
        verify_report = verify_email['report']
        print('Code completed !')
        if verify_report == True :
            Reddit_accounts.objects.create(
                username = username,
                profile_name = profile_name,
                password = password,
                email = new_email,
                avdname = self.emulator_name
            )
            return True