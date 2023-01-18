import difflib
import json
import os.path
import random
import re
import time

from appium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from appium.webdriver.common.touch_action import TouchAction
from surviral_avd.settings import BASE_DIR

from main import LOGGER
from accounts_conf import NORDVPN_ACCOUNTS


#  from twbot.utils import random_sleep


class NordVpn:
    def __init__(self, driver, user_avd):
        self.driver = driver
        self.user_avd = user_avd

    @staticmethod
    def get_driver():
        """
        Starts appium driver
        """
        path = '/wd/hub'
        port = 4723
        host = "http://localhost"
        opts = {
            "platformName": "Android",
            "platformVersion": "9",
            "deviceName": "android_116",
            "automationName": "UiAutomator2"
        }
        url = f"{host}:{port}{path}"
        driver = webdriver.Remote(url, desired_capabilities=opts, keep_alive=True)
        return driver

    @staticmethod
    def get_random_nord_vpn_server():
        server_list_file = os.path.join(BASE_DIR, "twbot", "vpn", "nord_vpn_servers_list.json")
        with open(server_list_file) as f:
            server_dict = json.load(f)
        random_country = random.choice(list(server_dict.keys()))
        random_server = random.choice(server_dict[random_country])
        return f"{random_country} #{random_server}"

    @staticmethod
    def get_random_nord_vpn_server_for_usa():
        server_list_file = os.path.join(BASE_DIR, "twbot", "vpn", "nord_vpn_servers_list.json")
        with open(server_list_file) as f:
            server_dict = json.load(f)
        random_country = "United States"
        random_server = random.choice(server_dict[random_country])
        return f"{random_country} #{random_server}"

    @staticmethod
    def get_server_list():
        server_list_file = os.path.join(BASE_DIR, "twbot", "vpn", "nord_vpn_servers_list.json")
        servers_list = []
        with open(server_list_file) as f:
            server_dict = json.load(f)
        for country, servers in server_dict.items():
            for server in servers:
                servers_list.append(f"{country} #{server}")
        return servers_list

    def check_app_installed(self, package):
        return self.driver.is_app_installed("com.nordvpn.android")

    def install_nord_vpn(self):
        apk_path = os.path.join(os.path.abspath(os.curdir), "../../apk/nord_vpn.apk")
        try:
            self.driver.install_app(apk_path)
            print("Nord VPN installed successfully")
        except Exception as e:
            print(f"Error:{e} while installing Nord Vpn apk")

    def connect_to_vpn(self, country_name, fail_tried=0, account=None):
        """
        It connect to VPN of given country
        :param country_name: Country name
        :return:
        """
        LOGGER.debug(f'Connect to vpn with country name: {country_name}')
        wait = WebDriverWait(self.driver, 20)
        if not account:
            account = random.choice(NORDVPN_ACCOUNTS)
        try:
            self.driver.start_activity("com.nordvpn.android", ".MainActivity")
            # self.wait_not_activity(".MainActivity", 20)
            try:
                self.wait_element_by_id("com.nordvpn.android:id/map_view", 10)
            except:
                pass
            time.sleep(2)
            # If not logged in it login
            self.login_to_vpn(country_name, fail_tried, account)
            time.sleep(5)
            self.wait_for_activity(".main.ControlActivity")
            cyber_sec_btn_id = self.driver.find_elements_by_id("com.nordvpn.android:id/primary_popup_cybersec_button")
            cyber_sec_btn_text = self.find_elements_by_text("ENABLE CYBERSEC")
            cyber_sec_btn = cyber_sec_btn_id or cyber_sec_btn_text
            cyber_sec_btn[0].click() if cyber_sec_btn else None
            self.do_scroll_down()
            LOGGER.debug(f'Find the cancel button')
            cancel_button = self.driver.find_elements_by_xpath(
                '//android.view.ViewGroup[@resource-id='
                '"com.nordvpn.android:id/toolbar"]/android.widget.ImageButton')
            if cancel_button:
                LOGGER.debug('click the cancel_button')
                cancel_button[0].click()
            if self.is_text_visible("Search"):
                search_button = self.find_elements_by_text("Search")
                search_button[0].click()
                self.wait_element_by_id("com.nordvpn.android:id/search_field")
                search_box = self.driver.find_element_by_id("com.nordvpn.android:id/search_field")
                search_box.send_keys(f"{country_name}")
                time.sleep(3)
                elements = self.driver.find_elements_by_id("com.nordvpn.android:id/name")
                if elements:
                    selected_country = False
                    for element in elements:
                        if re.search(f"{country_name}", element.text, re.I):
                            element.click()
                            selected_country = True
                            break
                    if not selected_country:
                        nord_vpn_countries = difflib.get_close_matches(country_name.split("#")[0],
                                                                       self.get_server_list())
                        country_name = random.choice(nord_vpn_countries)
                        self.user_avd.country = country_name
                        self.user_avd.save()
                else:
                    nord_vpn_countries = difflib.get_close_matches(country_name.split("#")[0], self.get_server_list())
                    country_name = random.choice(nord_vpn_countries)
                    self.user_avd.country = country_name
                    self.user_avd.save()

                time.sleep(3)
                if self.find_elements_by_text("LOG IN"):
                    self.login_to_vpn(country_name)
                    self.wait_element_by_id("com.nordvpn.android:id/name")
                    elements = self.driver.find_elements_by_id("com.nordvpn.android:id/name")
                    if elements:
                        for element in elements:
                            if re.search(f"{country_name}", element.text, re.I):
                                element.click()
                                break
                ok_btn_text = self.find_elements_by_text("OK")
                ok_btn_id = self.driver.find_elements_by_id("android:id/button1")
                ok_btn = ok_btn_text or ok_btn_id
                ok_btn[0].click() if ok_btn else None
            time.sleep(2)
            status_bar_id = self.driver.find_elements_by_id("com.nordvpn.android:id/status_bar_root_container")
            status_bar_xpath = self.driver.find_elements_by_xpath(
                "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android"
                ".widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.TextView")
            status_bar = status_bar_id or status_bar_xpath
            if status_bar:
                try:
                    wait.until(lambda d: re.search(f"Connected to {country_name}", status_bar[0].text, re.I))
                    print(status_bar[0].text)
                    # Enable block connections if VPN not connected
                    self.block_connections_without_vpn()
                    return True
                except Exception as e:
                    print(f"Error: {e}")
                    return False
            else:
                return
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            LOGGER.exception(e)
            #  print(f"Error: {e}")
            if self.check_429_error():
                NORDVPN_ACCOUNTS.remove(account)
                if NORDVPN_ACCOUNTS:
                    account = random.choice(NORDVPN_ACCOUNTS)
                    LOGGER.info(f'Connect to nord vpn again with another account: {account}')
                    return self.connect_to_vpn(country_name, fail_tried, account)
            return False

    def login_to_vpn(self, country_name, fail_tried=0, account=None):
        if not account:
            account = random.choice(NORDVPN_ACCOUNTS)
        LOGGER.debug(f'Login nord vpn with the account: {account}')
        try:
            time.sleep(2)
            login_button_id = self.driver.find_elements_by_id("com.nordvpn.android:id/login")
            login_button_text = self.find_elements_by_text("LOG IN")
            login_button = login_button_id or login_button_text
            if login_button:
                login_button[0].click()
                self.wait_till_text_visible("Terms of Service")
                self.wait_element_by_id("com.nordvpn.android:id/web_view_title", timeout=20)
                elements = self.driver.find_elements_by_xpath("//android.view.View")
                enter_email_address = True
                for element in elements:
                    if re.search("Choose an account to continue to NordVPN", element.text, re.I):
                        account_to_choose = self.driver.find_element_by_xpath(
                            "//android.view.View/android.widget.Button")
                        account_to_choose.click()
                        enter_email_address = False
                        break
                if enter_email_address:
                    # Email text boxes
                    input_boxes = self.find_elements_by_class_name("android.widget.EditText")
                    input_boxes[0].send_keys(account['username'])
                    continue_button = self.find_elements_by_text("Continue")
                    continue_button[0].click()

                time.sleep(1)
                self.wait_till_text_visible("Log In")
                # Password text boxes
                input_boxes = self.find_elements_by_class_name("android.widget.EditText")
                input_boxes[0].send_keys(account['password'])
                login_button = self.find_elements_by_text("Log In")
                login_button[0].click()
                time.sleep(10)
                #  random_sleep()
                LOGGER.debug(f'Close the update window')
                update_btn = self.driver.find_elements_by_id(
                    'com.nordvpn.android:id/primary_popup_update_button')
                if update_btn:
                    action = TouchAction(self.driver)
                    action.tap(x=100, y=100).perform()

                LOGGER.debug(f'Find the cancel button')
                cancel_button = self.driver.find_elements_by_xpath(
                    '//android.view.ViewGroup[@resource-id='
                    '"com.nordvpn.android:id/toolbar"]/android.widget.ImageButton')
                if cancel_button:
                    LOGGER.debug('click the cancel_button')
                    cancel_button[0].click()
                if self.wait_for_activity(".main.ControlActivity"):
                    return True
            else:
                time.sleep(10)
                LOGGER.debug(f'Close the update window')
                update_btn = self.driver.find_elements_by_id(
                    'com.nordvpn.android:id/primary_popup_update_button')
                if update_btn:
                    action = TouchAction(self.driver)
                    action.tap(x=100, y=100).perform()

                LOGGER.debug(f'Find the cancel button')
                cancel_button = self.driver.find_elements_by_xpath(
                    '//android.view.ViewGroup[@resource-id='
                    '"com.nordvpn.android:id/toolbar"]/android.widget.ImageButton')
                if cancel_button:
                    LOGGER.debug('click the cancel_button')
                    cancel_button[0].click()
                if self.wait_for_activity(".main.ControlActivity"):
                    return True
        except Exception as e:
            LOGGER.exception(e)
            #  print(f"Error: {e}")
            raise e
        return False

    def block_connections_without_vpn(self):
        self.driver.start_activity("com.android.settings", ".Settings$NetworkDashboardActivity")
        self.wait_for_activity(".Settings$NetworkDashboardActivity")
        advanced_btn_text = self.find_elements_by_text("Advanced")
        advanced_btn_xpath = self.driver.find_elements_by_xpath(
            "//android.widget.LinearLayout[6]/android.widget.RelativeLayout/android.widget.TextView[1]")
        advanced_btn = advanced_btn_text
        advanced_btn[0].click() if advanced_btn else None
        time.sleep(1)
        vpn_text = self.find_elements_by_text("VPN")
        vpn_xpath = self.driver.find_elements_by_xpath(
            "//android.widget.LinearLayout[6]/android.widget.LinearLayout/android.widget.RelativeLayout/android"
            ".widget.TextView[1]")
        vpn_btn = vpn_text or vpn_xpath
        vpn_btn[0].click() if vpn_btn else None
        self.wait_for_activity(".SubSettings", timeout=5)
        vpn_setting_id = self.driver.find_elements_by_id("com.android.settings:id/settings_button")
        vpn_setting_xpath = self.driver.find_elements_by_id(
            '//android.widget.ImageView[@content-desc="Settings"]')
        vpn_setting_btn = vpn_setting_id or vpn_setting_xpath
        vpn_setting_btn[0].click() if vpn_setting_btn else None
        time.sleep(2)
        always_vpn_on_switch = self.driver.find_elements_by_xpath('//android.widget.LinearLayout['
                                                                  '2]/android.widget.LinearLayout['
                                                                  '2]/android.widget.Switch')
        if always_vpn_on_switch:
            None if always_vpn_on_switch[0].get_attribute("checked") == "true" else always_vpn_on_switch[0].click()
            time.sleep(2)
        block_conections_switch = self.driver.find_elements_by_xpath('//android.widget.LinearLayout['
                                                                     '3]/android.widget.LinearLayout['
                                                                     '2]/android.widget.Switch')
        if block_conections_switch:
            if block_conections_switch[0].get_attribute("checked") == "false":
                block_conections_switch[0].click()
                time.sleep(2)
                turn_on_button_text = self.find_elements_by_text("TURN ON")
                turn_on_button_id = self.driver.find_elements_by_id("android:id/button1")
                turn_on_btn = turn_on_button_text or turn_on_button_id
                turn_on_btn[0].click() if turn_on_btn else None
                time.sleep(2)

    def wait_for_activity(self, activity, timeout=20, interval=1):
        try:
            WebDriverWait(self.driver, timeout, interval).until(
                lambda d: d.current_activity == activity
            )
            return True
        except TimeoutException:
            return False

    def find_elements_by_text(self, text):
        return self.driver.find_elements_by_android_uiautomator(f"new UiSelector().text(\"{text}\")")

    def is_text_visible(self, text):
        elements = self.driver.find_elements_by_android_uiautomator(f"new UiSelector().text(\"{text}\")")
        return True if elements else False

    def wait_element_by_xpath(self, xpath, timeout=20):
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def wait_element_by_id(self, element_id, timeout=20):
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located((By.ID, element_id)))

    def wait_not_activity(self, activity, timeout, interval=1):
        try:
            WebDriverWait(self.driver, timeout, interval).until(
                lambda d: d.current_activity != activity
            )
            return True
        except TimeoutException:
            return False

    def wait_till_text_visible(self, text, timeout=20, interval=1):
        try:
            WebDriverWait(self.driver, timeout, interval).until(
                lambda d: d.find_elements_by_android_uiautomator(f"new UiSelector().text(\"{text}\")")
            )
            return True
        except TimeoutException:
            return False

    def find_elements_by_class_name(self, class_name):
        return self.driver.find_elements_by_class_name(class_name)

    def do_scroll_down(self):
        size = self.driver.get_window_size()
        start_y = int(size["height"] * 0.4)
        end_y = int(size["height"] * 0.90)
        start_x = int(size["width"] * 0.90)
        end_x = int(size["width"] * 0.05)
        TouchAction(self.driver).press(x=start_x, y=end_y).wait(
            ms=500).move_to(x=start_x, y=start_y).release().perform()

    # 429 Too Many Requests
    def check_429_error(self):
        text = '429 Too Many Requests'
        LOGGER.debug('Checking the 429 error')
        if re.search(text, self.driver.page_source, re.MULTILINE | re.DOTALL):
            LOGGER.info(f'There is an error: {text}')
            return True


if __name__ == "__main__":
    driver = NordVpn.get_driver()
    # print(driver.current_activity)
    vpn = NordVpn(driver)
    vpn.connect_to_vpn("India")
