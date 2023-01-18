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
from conf import TWITTER_VERSIONS, RECAPTCHA_ALL_RETRY_TIMES
from conf import WAIT_TIME
from constants import COUNTRY_CODES
from exceptions import CannotStartDriverException
from twbot.models import *
from twbot.utils import *
from twbot.vpn.nord_vpn import NordVpn
from utils import get_installed_packages
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
        breakpoint()
        return True