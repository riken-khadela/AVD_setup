import json
import os
import random
import re
import string
import subprocess
import traceback
import urllib.request
from urllib.parse import urlencode

import requests
import unicodecsv
from appium.webdriver.common.mobileby import MobileBy
from appium.webdriver.webdriver import WebDriver
from django.db.models import Q
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from accounts_conf import *
from constants import XANALIA_TAGS
from exceptions import GetSmsCodeNotEnoughBalance
from main import LOGGER
from surviral_avd.settings import BASE_DIR
from twbot.models import TwitterActionLog, UserAvd, TwitterAccount
from twbot.models import Tweet, Comment, Phone, Sms
from utils import get_comment


def random_sleep(min_sleep_time=1, max_sleep_time=5):
    sleep_time = random.randint(min_sleep_time, max_sleep_time)
    LOGGER.debug(f'Random sleep: {sleep_time}')
    time.sleep(sleep_time)


def start_app(driver, app_name):
    LOGGER.info(f'Start the app: {app_name}')
    try:
        if app_name == 'twitter':
            driver().start_activity("com.twitter.android", "com.twitter.android.StartActivity")

        elif app_name == 'instagram':
            driver().start_activity("com.instagram.android", "com.instagram.mainactivity.LauncherActivity")

        elif app_name == 'surfshark':
            driver().start_activity("com.surfshark.vpnclient.android", ".StartActivity")

        elif app_name == 'webview':
            driver().start_activity('org.chromium.webview_shell', 'org.chromium.webview_shell.WebViewBrowserActivity')

        time.sleep(10)
    except Exception as e:
        pass


def close_app(driver, app_name):
    LOGGER.debug(f'Close the app: {app_name}')
    try:
        if app_name == 'twitter':
            driver().terminate_app("com.twitter.android")

        elif app_name == 'instagram':
            driver().terminate_app("com.instagram.android")

        elif app_name == 'surfshark':
            driver().terminate_app("com.surfshark.vpnclient.android")

        elif app_name == 'shadowsocks':
            driver().terminate_app("com.github.shadowsocks")

        time.sleep(10)
    except Exception as e:
        pass


def restart_app(driver, app_name):
    LOGGER.debug(f'Restart the app: {app_name}')
    if app_name == 'twitter':
        close_app(driver, 'twitter')
        start_app(driver, 'twitter')

    elif app_name == 'instagram':
        close_app(driver, 'instagram')
        start_app(driver, 'instagram')

    elif app_name == 'surfshark':
        close_app(driver, 'surfshark')
        start_app(driver, 'surfshark')


def goto_home(driver, tries=0):
    LOGGER.debug('goto home')
    retries = tries
    try:
        ele_one = driver().find_elements_by_xpath('//android.widget.LinearLayout[@content-desc="Home Tab"]')
        ele_two = driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View')
        ele_three = driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab. New items"]')

        # v9.9.0
        ele4 = driver().find_elements_by_accessibility_id('Home. New items')
        # v9.4.0
        ele5 = driver().find_elements_by_accessibility_id('Home')

        home_btn = ele_one or ele_two or ele_three or ele4 or ele5
        LOGGER.debug(f'home_btn: {home_btn}')
        if home_btn:
            home_btn[0].click()
        else:
            raise Exception('Cannot find home button')

        return driver
    except Exception as e:
        LOGGER.error(e)
        if retries >= 5:
            return False

        # click return icon to go to parent page
        return_icon_content_desc = 'Navigate up'
        click_element(driver, 'Return icon', return_icon_content_desc,
                      MobileBy.ACCESSIBILITY_ID)

        retries += 1
        if retries >= 5:
            restart_app(driver, 'twitter')

        goto_home(driver, tries=retries)


def goto_search(driver):
    LOGGER.debug('goto search box')
    retries = 0
    try:
        while True:
            retries += 1

            ele_one = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.view.ViewGroup/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.View')
            ele_two = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.view.ViewGroup/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]')

            # v9.9.0
            ele3 = driver().find_elements_by_accessibility_id('Search and Explore')

            search = ele_one or ele_two or ele3
            if search:
                search[0].click()
                #  time.sleep(5)
                random_sleep()
                break

            else:
                ele_one = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]')
                ele_two = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.View')
                search = ele_one or ele_two
                if search:
                    search[0].click()
                    #  time.sleep(5)
                    random_sleep()
                    break

                ele_root = driver().find_elements_by_id(
                    'com.twitter.android:id/tabs')
                if ele_root:
                    LOGGER.debug('Find search tab using tabbar element')
                    ele = ele_root[0].find_elements_by_xpath(
                        '//android.widget.LinearLayout/android.widget.LinearLayout[2]')
                    if ele:
                        ele[0].click()
                        break

                else:
                    restart_app(driver, "twitter")

            if retries >= 3:
                return False

    except Exception as e:
        print(e)


def search_for_target(driver, target):
    LOGGER.debug(f'search for "{target}"')
    # click on search bar
    ele_one = driver().find_elements_by_xpath('//android.widget.RelativeLayout[@content-desc="Search Twitter"]')
    ele_two = driver().find_elements_by_xpath(
        '//android.widget.RelativeLayout[@content-desc="Search Twitter"]/android.widget.TextView'
    )

    search = ele_one or ele_two
    search[0].click()
    #  time.sleep(5)
    random_sleep()

    # input search query in search bar
    search_bar = driver().find_elements_by_xpath('//android.widget.EditText[@content-desc="Search"]')
    search_bar[0].send_keys(str(target))
    press_enter(driver)
    #  time.sleep(5)
    random_sleep()

    # open searched profile
    LOGGER.debug('open tab people')
    ppl_xpath1 = driver().find_elements_by_xpath('//android.widget.LinearLayout[@content-desc="People"]')
    ppl_xpath2 = driver().find_elements_by_xpath(
        '//android.widget.LinearLayout[@content-desc="People"]/android.widget.TextView'
    )
    ppl_btn = ppl_xpath1 or ppl_xpath2
    ppl_btn[0].click()
    #  time.sleep(5)
    random_sleep()

    # open profile
    for j in range(random.randint(3, 7)):
        for i in range(random.randrange(3, 8)):
            profile_btn = driver().find_elements_by_xpath(
                f'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout'
                f'/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view'
                f'.ViewGroup/android.widget.LinearLayout/android.view.ViewGroup/androidx.viewpager.widget.ViewPager'
                f'/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview'
                f'.widget.RecyclerView/android.view.ViewGroup['
                f'{i}]/android.widget.RelativeLayout/android.widget.LinearLayout[1]/android.widget.TextView[1]')
            if profile_btn:
                profile_handle = profile_btn[0].text.replace("@", "").lower()
                if target.lower() == profile_handle:
                    LOGGER.debug('click profile button')
                    profile_btn[0].click()
                    #  time.sleep(5)
                    random_sleep()
                    return True

        LOGGER.debug('do some swipes')
        driver().swipe(start_x=random.randrange(50, 100), start_y=random.randrange(300, 350),
                       end_x=random.randrange(50, 100), end_y=random.randrange(0, 10), duration=600)
        #  time.sleep(2)
        random_sleep()

    return False


def click_search_tab(driver):
    LOGGER.debug('click search tab')
    ele_one = driver().find_elements_by_xpath(
        '//android.widget.RelativeLayout[@content-desc="Search Twitter"]')
    ele_two = driver().find_elements_by_xpath(
        '//android.widget.RelativeLayout[@content-desc="Search Twitter"]'
        '/android.widget.TextView'
    )
    ele3 = driver().find_elements_by_id(
        'com.twitter.android:id/query_view')
    ele4 = driver().find_elements_by_accessibility_id(
        'Search and Explore')
    ele5 = driver().find_elements_by_xpath(
        '//android.widget.FrameLayout[@resource-id="com.twitter.android:id/bottom_bar"]'
        '/android.view.ViewGroup/android.widget.HorizontalScrollView/'
        'android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.View'
    )
    ele6 = driver().find_elements_by_xpath(
        '//android.widget.HorizontalScrollView/android.widget.LinearLayout'
        '/android.widget.LinearLayout[2]/android.view.View')
    search = ele_one or ele_two or ele3 or ele4 or ele5 or ele6
    search[0].click()


def click_search_result_people_tab(driver):
    # open tab 'People'
    LOGGER.debug('Open tab People')
    people_xpath1 = driver().find_elements_by_xpath(
        '//android.widget.LinearLayout[@content-desc="People"]')
    people_xpath2 = driver().find_elements_by_accessibility_id(
        'People'
    )
    people_btn = people_xpath1 or people_xpath2
    people_btn[0].click()


def click_search_result_top_tab(driver):
    # open tab 'People'
    LOGGER.debug('Open tab Top')
    people_xpath1 = driver().find_elements_by_xpath(
        '//android.widget.LinearLayout[@content-desc="Top"]')
    people_xpath2 = driver().find_elements_by_accessibility_id('Top')
    people_btn = people_xpath1 or people_xpath2
    if people_btn:
        people_btn[0].click()


def check_search_result_is_empty(driver):
    try:
        empty_container = driver().find_element_by_id(
            'com.twitter.android:id/empty_container')
        LOGGER.info(f'Empty result for the keyword: {keyword}')
        return True
    except NoSuchElementException as e:
        return False


def get_search_result_from_tab_people(driver, want_at=False, content='text'):
    """Get texts or elements for the result"""
    accounts_elements = driver().find_elements_by_xpath(
        '//androidx.recyclerview.widget.RecyclerView/'
        'android.view.ViewGroup')
    #  accounts = {}
    accounts = []
    for element in accounts_elements:
        try:
            name = element.find_element_by_id(
                'com.twitter.android:id/name_item').text
            screen_name = element.find_element_by_id(
                'com.twitter.android:id/screenname_item').text
            try:
                description = element.find_element_by_id(
                    'com.twitter.android:id/profile_description_item').text
            except NoSuchElementException as e:
                description = ''
            if screen_name.startswith('@') and not want_at:
                screen_name = screen_name[1:]

            LOGGER.debug(f'name: {name}, screen_name: {screen_name}')
            LOGGER.debug(f'description: {description}')

            if content == 'text':
                #  accounts[screen_name] = {
                #          'name': name,
                #          'screen_name': screen_name,
                #          'description': description}
                accounts.append({
                    'name': name,
                    'screen_name': screen_name,
                    'description': description})
            else:
                #  accounts[screen_name] = {
                #          'name': name,
                #          'screen_name': screen_name,
                #          'description': description,
                #          'element': element}
                accounts.append({
                    'name': name,
                    'screen_name': screen_name,
                    'description': description,
                    'element': element})
            #  LOGGER.debug(f'accounts: {accounts}')
        except Exception as e:
            LOGGER.warning(e)
    return accounts


def get_search_result_from_suggestion(driver, account_name, want_at=False,
                                      content='text'):
    """Get texts or elements for the suggestion list"""
    LOGGER.debug('Get accounts items from search suggestion list')
    list_id = 'com.twitter.android:id/search_suggestions_list'
    list_class = 'androidx.recyclerview.widget.RecyclerView'
    list_item_xpath = (f'//{list_class}[@resource-id="{list_id}"]/*')
    accounts_elements = driver().find_elements_by_xpath(list_item_xpath)
    accounts = []
    for element in accounts_elements:
        try:
            name = element.find_element_by_id(
                'com.twitter.android:id/name_item').text
            screen_name = element.find_element_by_id(
                'com.twitter.android:id/screenname_item').text
            if screen_name.startswith('@') and not want_at:
                screen_name = screen_name[1:]

            LOGGER.debug(f'name: {name}, screen_name: {screen_name}')

            if screen_name and account_name.lower() == screen_name.lower():
                if content == 'text':
                    accounts.append({
                        'name': name,
                        'screen_name': screen_name})
                else:
                    accounts.append({
                        'name': name,
                        'screen_name': screen_name,
                        'element': element})
                LOGGER.debug(f'accounts: {accounts}')
                return accounts
        except Exception as e:
            LOGGER.warning(e)

        try:
            title_element = element.find_element_by_id(
                'com.twitter.android:id/title')
            text = title_element.text
            compare_name = account_name if account_name.startswith('@') else '@' + account_name
            compare_text = f'go to {compare_name}'
            if text and compare_name.lower() in text.lower():
                if content == 'text':
                    accounts.append({
                        'name': account_name,
                        'screen_name': account_name})
                else:
                    accounts.append({
                        'name': account_name,
                        'screen_name': account_name,
                        'element': title_element})
                LOGGER.debug(f'accounts: {accounts}')
                return accounts
        except Exception as e:
            LOGGER.warning(e)

    return accounts


def search(text, driver):
    # input search query in search bar
    LOGGER.debug(f'Input search text: {text}')
    search_bar = driver().find_elements_by_xpath(
        '//android.widget.EditText[@content-desc="Search"]')
    search_bar1 = driver().find_element_by_id(
        'com.twitter.android:id/query')
    search_bar = search_bar or search_bar1
    search_bar[0].clear()
    search_bar[0].send_keys(text)
    press_enter(driver)


def search_without_enter(text, driver):
    # input search query in search bar
    LOGGER.debug(f'Input search text: {text}')
    search_bar = driver().find_elements_by_xpath(
        '//android.widget.EditText[@content-desc="Search"]')
    search_bar1 = driver().find_element_by_id(
        'com.twitter.android:id/query')
    search_bar = search_bar or search_bar1
    search_bar[0].clear()
    search_bar[0].send_keys(text)


def open_profile_by_search(account_name, driver, do_goto_home=True,
                           do_goto_search=True):
    if do_goto_home:
        goto_home(driver)

    if do_goto_search:
        goto_search(driver)
        click_search_tab(driver)

    search_without_enter(account_name, driver)
    random_sleep(5, 10)
    #  random_sleep(10, 20)
    # get accounts from suggestion list
    accounts = get_search_result_from_suggestion(driver, account_name, content='element')
    for account in accounts:
        screen_name = account['screen_name']
        if screen_name.strip().lower() == account_name.strip().lower():
            LOGGER.debug('Click one item of suggestion list')
            account['element'].click()
            return True

    press_enter(driver)
    click_search_result_people_tab(driver)
    random_sleep(10, 20)
    results = get_search_result_from_tab_people(driver, content='element')
    #  LOGGER.debug(f'results: {results}')
    for account in results:
        screen_name = account['screen_name']
        if screen_name.strip().lower() == account_name.strip().lower():
            LOGGER.debug('Click one item of research result')
            account['element'].click()
            return True

    return False


def swipe_up_element(driver, element, times=1, duration=5000, delta=10,
                     end_y=None):
    location = element.location
    size = element.size

    start_x = location['x'] + size['width'] // 2
    start_y = location['y'] + size['height']
    end_x = start_x
    if not end_y:
        end_y = location['y']

    while times > 0:
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y},'
                     f' end_x: {end_x}, end_y: {end_y}')
        try:
            driver().swipe(start_x, start_y, end_x, end_y, duration=duration)
        except InvalidElementStateException as e:
            LOGGER.error(e)
            driver().swipe(start_x, start_y - delta, end_x, end_y, duration=duration)
        times -= 1


def swipe_up_search_result(driver, times=1, duration=5000):
    LOGGER.debug('Swipe up element of search result list')
    result_element = driver().find_element_by_id(
        'android:id/list')
    swipe_up_element(driver, result_element, times, duration)


def open_messages(driver):
    pass


def open_notification(driver):
    pass


def open_target(driver, target):
    pass


def check_conditions(driver):
    pass


def press_enter(driver):
    driver().press_keycode(66)


def connect_vpn(driver, country):
    try:
        acc_email = 'admin@noborders.net'
        acc_pass = 'Surviraladmin789'

        # Launch surfshark
        start_app(driver, 'surfshark')

        # Login if required
        login_retries = 0
        while True:
            login_retries += 1

            login_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/onboarding_login_action')
            login_btn_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.TextView')

            if login_btn_id or login_btn_xpath:
                login_btn = login_btn_id or login_btn_xpath
                login_btn[0].click()
                time.sleep(3)

                email_input_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/login_email')
                email_input_xpath = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.ScrollView/android.view.ViewGroup/android.widget.LinearLayout[1]/android.widget.FrameLayout/android.widget.EditText')
                email_input = email_input_id or email_input_xpath
                email_input[0].send_keys(acc_email)
                time.sleep(3)

                password_input_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/login_password')
                password_input_xpath = driver().find_elements_by_id('//android.widget.EditText[@content-desc=" "]')
                password_input = password_input_id or password_input_xpath
                password_input[0].send_keys(acc_pass)
                time.sleep(3)

                login_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/login_menu')
                login_btn_xpath = driver().find_elements_by_id(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.view.ViewGroup/androidx.appcompat.widget.LinearLayoutCompat/android.widget.TextView')
                login_btn = login_btn_id or login_btn_xpath
                login_btn[0].click()
                time.sleep(7)

                alert_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/alertTitle')
                alert_xpath = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.appcompat.widget.LinearLayoutCompat/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
                if not alert_id and not alert_xpath:
                    break

            if login_retries >= 3:
                return False

            else:
                break

        # Connect VPN
        connect_retires = 0
        while True:
            connect_retires += 1

            # check if vpn is already connected
            current_server_name_id = driver().find_elements_by_id(
                'com.surfshark.vpnclient.android:id/current_server_name')
            current_server_name_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.TextView')

            if current_server_name_id or current_server_name_xpath:
                current_server = current_server_name_id or current_server_name_xpath

                if country in current_server[0].text:
                    return True
                else:
                    # Disconnect vpn
                    disconnect_btn = driver().find_elements_by_id(
                        'com.surfshark.vpnclient.android:id/main_disconnect_action')
                    if disconnect_btn:
                        disconnect_btn[0].click()
                        time.sleep(3)
                    else:
                        return False

            restart_app(driver, 'surfshark')
            time.sleep(10)

            location_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/navigation_locations')
            location_btn_xpath1 = driver().find_elements_by_xpath(
                '//android.widget.FrameLayout[@content-desc="Locations"]/android.widget.ImageView')
            location_btn_xpath2 = driver().find_elements_by_xpath(
                '//android.widget.FrameLayout[@content-desc="Locations"]')

            if location_btn_id or location_btn_xpath1 or location_btn_xpath2:
                location_btn = location_btn_id or location_btn_xpath1 or location_btn_xpath2
                location_btn[0].click()
                time.sleep(3)

            search_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/serverlist_search')
            search_btn_xpath = driver().find_elements_by_xpath('//android.widget.TextView[@content-desc="Search"]')

            if search_btn_id or search_btn_xpath:
                search_btn = search_btn_id or search_btn_xpath
                search_btn[0].click()
                time.sleep(3)

            search_bar_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/search_src_text')
            search_bar_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup[1]/androidx.appcompat.widget.LinearLayoutCompat/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.EditText')
            if search_bar_xpath or search_bar_id:
                search_bar = search_bar_xpath or search_bar_id
                search_bar[0].send_keys(country)
                time.sleep(3)

            country_btn_xpath1 = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup[2]/android.view.ViewGroup/android.widget.FrameLayout/android.widget.RelativeLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]')
            country_btn_xpath2 = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup[2]/android.view.ViewGroup/android.widget.FrameLayout/android.widget.RelativeLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.widget.TextView')

            if country_btn_xpath1 or country_btn_xpath2:
                country_btn = country_btn_xpath1 or country_btn_xpath2
                country_btn[0].click()
                time.sleep(25)
            else:
                print(f"{country} is not available in surfshark list.")
                return False

            # Check connection accept alert
            connection_alert_id = driver().find_elements_by_id('android:id/alertTitle')
            connection_alert_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
            connection_alert = connection_alert_id or connection_alert_xpath
            if connection_alert:
                accept_btn_id = driver().find_elements_by_id('android:id/button1')
                accept_btn_xpath = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[2]')
                accept_btn = accept_btn_id or accept_btn_xpath
                if accept_btn:
                    accept_btn[0].click()
                    time.sleep(5)

            # close avoid connection issue alert
            connection_issue_xpath = driver().find_elements_by_id(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.TextView[1]')
            if connection_issue_xpath:
                if connection_issue_xpath[0].text == "Avoid potential connection issues":
                    close_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/close')
                    close_btn_xpath = driver().find_elements_by_xpath(
                        '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.TextView[4]')
                    close_btn = close_btn_id or close_btn_xpath
                    close_btn[0].click()
                    time.sleep(5)

            # Make sure that connection was successfull
            connection_status_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/connection_status')
            connection_status_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout[2]/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
            connection_status = connection_status_id or connection_status_xpath
            if connection_status:
                if connection_status[0].text.lower() == "connected":
                    return True

            if connect_retires >= 3:
                print(f"Couldn't connect vpn in 3 tries.")
                return False

    except Exception as e:
        print(e)
        return False


def get_random_wait_time(min, max):
    random_time = random.randrange(min, max)
    time.sleep(random_time)


'''
*****************************************
GETSMSCODE FOR TWITTER
*****************************************
'''


def get_summary():
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "login",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
    }
    #  payload = urlencode(payload)
    #  full_url = url + payload
    response = requests.post(url, data=payload)
    response = response.content.decode("utf-8")

    return response


def get_mobile_list():
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "mobilelist",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
    }
    #  payload = urlencode(payload)
    #  full_url = url + payload
    response = requests.post(url, data=payload)
    response = response.content.decode("utf-8")

    return response


def get_twitter_number(mobile=None, pid=GETSMSCODE_PID):
    url = "http://api.getsmscode.com/usdo.php?"
    if mobile:
        payload = {
            "action": "getmobile",
            "username": "pay@noborders.net",
            "token": GETSMSCODE_API_KEY,
            "pid": pid,
            "mobile": mobile
        }
    else:
        payload = {
            "action": "getmobile",
            "username": "pay@noborders.net",
            "token": GETSMSCODE_API_KEY,
            "pid": pid,
        }
    payload = urlencode(payload)
    full_url = url + payload
    response = requests.post(url=full_url)
    response = response.content.decode("utf-8")

    LOGGER.debug(f'Response when getting number: {response}, pid: {pid}')
    try:
        Phone.objects.get_or_create(number=response, pid=pid)
    except Exception as e:
        LOGGER.error(e)

    return response


def get_twitter_number_ui(mobile=None, pids=('66', GETSMSCODE_PID), retry_times=3):
    # retry 3 times to get phone number
    # error: +Message|unavailable
    pids = list(pids)
    while retry_times > 0:
        if len(pids) == 0:
            pid = GETSMSCODE_PID
        else:
            pid = pids.pop()
        LOGGER.debug(f'The pid to get phone number: {pid}')
        phone = get_twitter_number(pid=pid)
        if "balance is not enough" in phone:
            raise GetSmsCodeNotEnoughBalance
        LOGGER.debug(f'phone number: {phone}')
        if 'unavailable' in phone:
            random_sleep(20, 30)
            retry_times -= 1
        else:  # otherwise got the right number
            return phone, pid
            break
        if retry_times <= 0:
            LOGGER.critical('Cannot get valid phone number,'
                            ' now stop the bot')
    return '', ''


def save_sms(phone, sms, pid, purpose=None):
    if purpose:
        LOGGER.debug(f'Save phone and sms for "{purpose}": {phone}, {pid}, {sms}')
    else:
        LOGGER.debug(f'Save phone and sms: {phone}, {pid}, {sms}')

    users = TwitterAccount.objects.filter(phone=phone)
    if len(users) == 1:
        user = users[0]
    else:
        user = None

    if user:
        (number, created) = Phone.objects.get_or_create(
            number=phone, pid=pid, user=user)
    else:
        (number, created) = Phone.objects.get_or_create(
            number=phone, pid=pid)

    if purpose:
        Sms.objects.get_or_create(number=number, content=sms, purpose=purpose)
    else:
        Sms.objects.get_or_create(number=number, content=sms)


def get_twitter_sms(phone_number, pid=GETSMSCODE_PID, purpose=None):
    # Do not Request Get SMS Fast , Every 10s is best.
    # Too Fast will be block our system
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "getsms",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
        "pid": pid,
        "mobile": phone_number,
        "author": "pay@noborders.net",
    }
    payload = urlencode(payload)
    full_url = url + payload
    for x in range(10):
        response = requests.post(url=full_url).text
        LOGGER.debug(f'SMS content for {phone_number}: {response}')
        #  print(response)
        save_sms(phone_number, response, pid, purpose)
        code = [int(s) for s in response.split() if s.isdigit() if len(s) == 6 if s != 40404]
        if code:
            LOGGER.debug(f'SMS code for {phone_number}: {code[0]}')
            return code[0]
        if 'code is' in response:
            otp = response.split("code is ")[1][:6]
            LOGGER.debug(f'SMS code for {phone_number}: {otp}')
            return otp
        time.sleep(4)

    return False


def ban_twitter_number(phone_number, pid=GETSMSCODE_PID):
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "addblack",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
        "pid": GETSMSCODE_PID,
        "mobile": phone_number,
        "author": "pay@noborders.net",
    }
    payload = urlencode(payload)
    full_url = url + payload
    response = requests.post(url=full_url)
    # save the result
    try:
        Phone.objects.update_or_create(number=phone_number, pid=pid,
                                       is_banned=True, ban_result=response)
    except Exception as e:
        LOGGER.error(e)
    return response


def get_random_password():
    alphaneumeric_characters = string.ascii_letters + string.digits
    result_str = 'Ang1' + ''.join(random.choice(alphaneumeric_characters) for i in range(4))
    return result_str


def get_real_random_password(passwd_start_len=8, passwd_end_len=20):
    pw_len = random.randint(passwd_start_len, passwd_end_len)
    all_char_set = string.digits + string.ascii_letters + string.punctuation
    pw_char_set = all_char_set.replace('\\', '')
    random_pw = ''.join(random.choices(pw_char_set, k=pw_len))
    return random_pw


def get_random_username():
    url = "https://randommer.io/Name"
    full_name = requests.post(url, data={"number": 1, "type": "fullname"}).json()[0]
    return full_name


def delete_download_files(port):
    LOGGER.debug('Delete all files in directory Download')
    cmd = f'adb -s emulator-{port} shell rm -rf /storage/emulated/0/Download/*'
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p.wait()
    return True


def push_image_to_device(file_path, port):
    LOGGER.debug(f'Push the file to directory Download: {file_path}')
    cmd = f'adb -s emulator-{port} push {file_path} /storage/emulated/0/Download/'
    LOGGER.debug(cmd)
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p.wait()
    return True


def download_image(url, image_name):
    local_path = os.path.join(BASE_DIR, 'images/' + image_name)
    LOGGER.debug(f'Download "{local_path}" from "{url}"')
    urllib.request.urlretrieve(url, local_path)


import time
from functools import wraps


def retry(tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            max_tries, max_delay = tries, delay
            while max_tries > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), max_delay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(max_delay)
                    max_tries -= 1
                    max_delay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def log_activity(avd_id, action_type, msg, error):
    try:
        details = {
            "avd_id": avd_id,
            "action_type": action_type,
            "action": msg,
            "error": error,
        }
        LOGGER.debug(f'Log Activity: {details}')
        TwitterActionLog.objects.create(**details)
    except Exception as e:
        print(e)


def terminate_device(port):
    cmd = f'lsof -t -i tcp:{port} | xargs kill -9'
    process = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    process.wait()


def terminate_appium(port):
    # get appium running pid
    try:
        cmd = f"ss -l -p -n | grep {port}"
        output = subprocess.getoutput(cmd)
        pid = output.split("pid=")[-1].split(",")[0]
    except:
        pass

    # kill process
    if pid:
        cmd = f"kill -9 {pid}"
        process = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        process.wait()
        time.sleep(2)


def swipe_up_half_screen(driver, duration=2000):
    size = driver().get_window_size()
    position = driver().get_window_position()

    x = position['x']
    y = position['y']
    width = size['width']
    height = size['height']

    LOGGER.debug(f'x: {x}, y: {y}, width: {width}, height: {height}')

    start_x = x + width // 2
    start_y = y + int(height * 0.8)
    end_x = start_x
    end_y = y + int(height * 0.2)

    LOGGER.debug(f'start_x: {start_x}, start_y: {start_y},'
                 f' end_x: {end_x}, end_y: {end_y}')

    driver().swipe(start_x, start_y, end_x, end_y, duration)
    time.sleep(1)


def swipe_up(driver):
    size = driver().get_window_size()
    x = size['width']
    y = size['height']

    x1 = x * 0.5
    y1 = y * 0.8
    y2 = x * 0.1
    t = 5000

    driver().swipe(x1, y1, x1, y2, t)
    time.sleep(1)


def swipe_down(driver):
    size = driver().get_window_size()
    x = size['width']
    y = size['height']

    x1 = x * 0.5
    y1 = y * 0.1
    y2 = y * 0.8
    t = 5000

    driver().swipe(x1, y1, x1, y2, t)
    time.sleep(1)


def perform_random_action(driver, bot_name):
    """Search one random topic, and select some tweets in the tab latest,
    then like them.
    """
    LOGGER.debug('perform random actions')
    try:
        followed_accounts = []

        # tags_list = XANALIA_TAGS + CAZICAZI_TAGS
        tags_list = XANALIA_TAGS

        n_likes = random.randrange(4, RANDOM_LIKE_MAX_NUMBER)
        n_follows = random.randrange(4, RANDOM_FOLLOW_MAX_NUMBER)
        search_tag = random.choice(tags_list)

        LOGGER.debug(f'n_likes: {n_likes}, n_follows: {n_follows},'
                     f' search_tag: {search_tag}')

        goto_home(driver)
        goto_search(driver)

        # click on search bar
        #  LOGGER.debug('click on search bar')
        click_search_tab(driver)
        random_sleep()

        # input search query in search bar
        #  LOGGER.debug('input search query in search bar')
        search_without_enter(search_tag, driver)
        press_enter(driver)
        #  time.sleep(3)
        random_sleep(5)

        # open searched profile
        LOGGER.debug('open searched profile')
        latest_xpath1 = driver().find_elements_by_xpath('//android.widget.LinearLayout[@content-desc="Latest"]')
        latest_xpath2 = driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Latest"]/android.widget.TextView'
        )
        latest_btn = latest_xpath1 or latest_xpath2
        LOGGER.debug('click tab latest')
        latest_btn[0].click()
        #  time.sleep(3)
        random_sleep()

        # Like posts
        LOGGER.debug('Like posts')
        total_followed = 0
        liked = 0
        total_tries = 0

        while True:
            total_tries += 1

            if total_tries >= (liked + 7):
                LOGGER.debug(f'total_tries: {total_tries}, liked: {liked}')
                LOGGER.debug(f'total_tries >= (liked + 7), now break loop')
                break

            if liked >= n_likes:
                LOGGER.debug(f'n_likes: {n_likes}, liked: {liked}')
                LOGGER.debug(f'liked >= n_likes, now break loop')
                break

            # get all tweets on the page
            # wait the element appear
            if hasattr(driver, '__self__') and hasattr(driver.__self__, 'wait_obj'):
                LOGGER.debug('Wait for search result')
                locator_type = By.ID
                element_locator = 'com.twitter.android:id/outer_layout_row_view_tweet'
                try:
                    element = driver.__self__.wait_obj.until(EC.presence_of_element_located(
                        (locator_type, element_locator)))
                except Exception as e:
                    LOGGER.exception(e)

            tweets = driver().find_elements_by_id('com.twitter.android:id/outer_layout_row_view_tweet')
            LOGGER.debug(f'len(tweets): {len(tweets)}')

            # loop over the tweets and like them
            for x in range(len(tweets)):
                # Open tweet
                LOGGER.debug('Open tweet')
                refreshed_tweets = driver().find_elements_by_id('com.twitter.android:id/outer_layout_row_view_tweet')
                tweet = refreshed_tweets[x]
                element_xy_bounds = tweet.get_attribute('bounds')
                element_coordinates = element_xy_bounds.replace("'", " ").replace("][", ",").replace("[", " ").replace(
                    "]", " ").replace(" ", "").split(",")
                x1 = int(element_coordinates[0])
                y1 = int(element_coordinates[1])
                driver().tap([(x1, y1)])
                time.sleep(2)

                # Follow Process
                if total_followed <= n_follows:
                    profile_btn_id_1 = driver().find_elements_by_id('com.twitter.android:id/name')
                    profile_btn_id_2 = driver().find_elements_by_id('com.twitter.android:id/screen_name')
                    profile_btn = profile_btn_id_1 or profile_btn_id_2
                    profile_btn[0].click()
                    time.sleep(5)

                    follow_btn_id = driver().find_elements_by_id('com.twitter.android:id/button_bar_follow')
                    follow_btn_acc_id = driver().find_elements_by_accessibility_id('Follow MOBOX. Follow.')
                    follow_btn_xpath = driver().find_elements_by_xpath(
                        '//android.widget.Button[@content-desc="Follow MOBOX. Follow."]')
                    follow_btn = follow_btn_id or follow_btn_acc_id or follow_btn_xpath
                    if follow_btn:
                        follow_btn[0].click()
                    time.sleep(1)

                    # get username of account on which action is being performed
                    account_username_id = driver().find_elements_by_id('com.twitter.android:id/user_name')
                    account_username_xpath = driver().find_elements_by_xpath(
                        '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.FrameLayout[1]/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.TextView')
                    account_username = account_username_id or account_username_xpath
                    account_username = account_username[0].text.replace('@', '')
                    if account_username not in followed_accounts:
                        followed_accounts.append(account_username)
                    time.sleep(1)

                    driver().press_keycode(4)
                    time.sleep(1)

                # Liking process
                for i in range(5):
                    time.sleep(2)

                    # check if already liked
                    already_liked_btn_accs_id = driver().find_elements_by_accessibility_id('Like (Liked)')
                    already_liked_btn_xpath = driver().find_elements_by_xpath(
                        '//android.widget.ImageButton[@content-desc="Like (Liked)"]')
                    already_liked = already_liked_btn_xpath or already_liked_btn_accs_id
                    if not already_liked:
                        # find like button
                        like_btn_accs_id = driver().find_elements_by_accessibility_id('Like')
                        like_btn_xpath = driver().find_elements_by_xpath(
                            '//android.widget.ImageButton[@content-desc="Like"]')
                        like_btn = like_btn_accs_id or like_btn_xpath

                        if like_btn:
                            like_btn[0].click()
                            liked += 1
                            break
                        else:
                            swipe_up(driver)

                driver().press_keycode(4)

            swipe_up(driver)

        goto_home(driver)

        # Write random action data in csv
        # followed_accounts_str = ""
        # for x in followed_accounts:
        #     if not followed_accounts_str:
        #         followed_accounts_str = x
        #     else:
        #         followed_accounts_str += ", " + x
        # write_output([UserAvd.objects.get(name=bot_name).twitter_account.screen_name, followed_accounts[1:], search_tag, len(followed_accounts[1:]), len(followed_accounts[1:])], f"random_action_{str(datetime.date.today())}")

        TwitterActionLog.objects.create(
            avd=UserAvd.objects.get(name=bot_name),
            action_type='RANDOM_ACTION',
            action="",
            msg={search_tag: followed_accounts},
            status='SUCCESS',
            error={'msg': ''}
        )
        return True

    except Exception as e:
        tb = traceback.format_exc()
        TwitterActionLog.objects.create(
            avd=UserAvd.objects.get(name=bot_name),
            action_type='RANDOM_ACTION',
            action='',
            status='FAIL',
            error={'msg': str(tb)}
        )
        LOGGER.exception(e)
        return False


def get_random_profile_banner_image():
    pages_list = [x for x in range(20)]
    banner_query_list = ["mountain",
                         "universe",
                         "forest",
                         "waterfall",
                         "river",
                         "pets",
                         "cats",
                         "wild",
                         "abstract",
                         "group",
                         ]

    random.shuffle(pages_list)
    page = random.choice(pages_list)
    profile_data = requests.get(
        url="https://api.unsplash.com/search/photos/?client_id=35p1IHnOOwBqsSYny6EAteB9EpApVsiWwZLzefiG0sA&query"
            f"=face&per_page=50&page={page} "
    )
    time.sleep(3)
    profile_data = json.loads(profile_data.content.decode('utf-8'))
    profile_image_list = [x['urls']['regular'] for x in profile_data.get('results')]

    random.shuffle(pages_list)
    random.shuffle(banner_query_list)
    page = random.choice(pages_list)
    query = random.choice(banner_query_list)
    banner_data = requests.get(
        url=f"https://api.unsplash.com/search/photos/?client_id=35p1IHnOOwBqsSYny6EAteB9EpApVsiWwZLzefiG0sA&query"
            f"={query}&per_page=50&page={page} "
    )
    time.sleep(3)
    banner_data = json.loads(banner_data.content.decode('utf-8'))
    banner_image_list = [x['urls']['regular'] for x in banner_data.get('results')]

    return profile_image_list, banner_image_list


def update_blank_images():
    ta_qs = TwitterAccount.objects.filter(Q(profile_image__isnull=True)
                                          | Q(banner_image__isnull=True)
                                          )
    if ta_qs:
        count = ta_qs.count()
        profiles, banners = [], []
        while len(profiles) <= count and len(banners) <= count:
            profiles_list, banners_list = get_random_profile_banner_image()
            profiles += profiles_list
            banners += banners_list

        for x, ta in enumerate(ta_qs):
            ta.profile_image = profiles[x]
            ta.banner_image = banners[x]
            ta.save()


def string_to_int(number_str):
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}

    number_str = number_str.replace(",", "")

    if number_str[-1].isdigit():
        return int(number_str)

    mult = multipliers[number_str[-1]]
    return int(float(number_str[:-1]) * mult)


def write_output(data, file_name):
    write_mode = "ab"
    logs_folder = "../logs"

    if not os.path.exists(logs_folder):
        os.mkdir(logs_folder)

    file_path = logs_folder + "/" + file_name + ".csv"

    with open(file_path, mode=write_mode) as csvFile:
        row = unicodecsv.writer(csvFile, delimiter=",", lineterminator="\n")
        row.writerow(data)


def get_real_driver(driver):
    if isinstance(driver, WebDriver):
        return driver
    else:
        return driver()


def find_element(driver, element, locator, locator_type=By.XPATH, page=None,
                 timeout=10):
    """Waint for an element, then return it or None"""
    driver = get_real_driver(driver)
    wait_obj = WebDriverWait(driver, timeout)
    try:
        ele = wait_obj.until(
            EC.presence_of_element_located(
                (locator_type, locator)))
        if page:
            LOGGER.debug(
                f'Find the element "{element}" in the page "{page}"')
        else:
            LOGGER.debug(f'Found the element: {element}')
        return ele
    except (NoSuchElementException, TimeoutException) as e:
        if page:
            LOGGER.warning(f'Cannot find the element "{element}"'
                           f' in the page "{page}"')
        else:
            LOGGER.warning(f'Cannot find the element: {element}')


def click_element(driver, element, locator, locator_type=By.XPATH,
                  timeout=10):
    driver = get_real_driver(driver)
    """Find an element, then click and return it, or return None"""
    ele = find_element(driver, element, locator, locator_type, timeout=timeout)
    if ele:
        ele.click()
        LOGGER.debug(f'Click the element: {element}')
        return ele


def find_page(driver, page, element, locator, locator_type=By.XPATH, timeout=10):
    """Find en element of a page, then return it or return None"""
    return find_element(driver, element, locator, locator_type, page, timeout)


def find_element_from_parent(parent_element, element, locator,
                             locator_type=By.XPATH):
    """Find child element from parent, then return it or None"""
    try:
        ele = parent_element.find_element(by=locator_type, value=locator)
        LOGGER.debug(f'Found the element: {element}')
        return ele
    except NoSuchElementException as e:
        LOGGER.warning(f'Cannot find the element: {element}')


def check_pinned_tweet(tweet_element):
    #  pin_icon_id = 'com.twitter.android:id/social_context_badge'
    #  if find_element_from_parent(tweet_element, 'pinned tweet',
    #          pin_icon_id, By.ID):
    #      return tweet_element

    content = tweet_element.get_attribute('content-desc')
    LOGGER.debug(f'content: {content}')
    if '. . . . Pinned Tweet.' in content:
        LOGGER.debug('Find pinned tweet by content-desc')
        return tweet_element


def check_promoted_tweet(driver, tweet_element):
    promote_id = 'com.twitter.android:id/tweet_promoted_badge'
    if find_element_from_parent(tweet_element, 'promoted tweet',
                                promote_id, By.ID):
        return tweet_element

    promote_id1 = 'com.twitter.android:id/tweet_promoted_badge_bottom'
    if find_element_from_parent(tweet_element, 'promoted tweet',
                                promote_id1, By.ID):
        return tweet_element

    content = tweet_element.get_attribute('content-desc')
    LOGGER.debug(f'content: {content}')
    if '. . . Promoted.' in content:
        LOGGER.debug('Find promoted tweet by content-desc')
        return tweet_element

    promote_frame_xpath = ('//android.widget.TextView'
                           '[@resource-id="com.twitter.android:id/title"]/..')
    title_id = 'com.twitter.android:id/title'
    ele = find_element(driver, 'title', title_id, By.ID)
    if ele:
        if 'Promoted Tweet' in ele.text:
            LOGGER.debug(f'Find promoted tweet by title: {ele.text}')
            return driver().find_element_by_xpath(promote_frame_xpath)


def ignore_pinned_promoted_tweet(driver, tweet_element):
    flag = False
    ele = check_pinned_tweet(tweet_element)
    if ele:
        LOGGER.debug('Ignore one pinned tweet')
        swipe_up_element(driver, ele)
        return True

    ele = check_promoted_tweet(driver, tweet_element)
    if ele:
        LOGGER.debug('Ignore one promoted tweet')
        swipe_up_element(driver, ele)
        return True

    return flag


def get_latest_tweet1(driver):
    LOGGER.debug('Get latest tweet other than pinned or promoted tweet')

    while True:
        random_sleep()
        tweet_elements = driver().find_elements_by_id("com.twitter.android:id/row")
        if not tweet_elements:
            LOGGER.error('Cannot find tweet element')
            return None

        for tweet_element in tweet_elements:
            if ignore_pinned_promoted_tweet(driver, tweet_element):
                continue
            else:
                return tweet_element


def get_latest_tweet(driver):
    LOGGER.debug('Get latest tweet other than pinned or promoted tweet')

    times = 0
    while True:
        random_sleep()
        tweet_elements = driver().find_elements_by_id("com.twitter.android:id/row")
        if not tweet_elements:
            LOGGER.error('Cannot find tweet element')
            return None

        element = None
        for tweet_element in tweet_elements:
            if check_pinned_tweet(tweet_element) or check_promoted_tweet(
                    driver, tweet_element):
                element = tweet_element
                continue
            else:
                return tweet_element

        #  swipe_up(driver)
        #  element = driver().find_element_by_id(
        #          'com.twitter.android:id/outer_layout_row_view_tweet')
        if element:
            swipe_up_element(driver, element, duration=2000)
        #  swipe_up_half_screen(driver)
        times += 1
        if times > 20:
            LOGGER.error('Some error happened, and exit loop')
            break


def check_element_is_tweet_element(element):
    tweet_row_id = 'com.twitter.android:id/row'
    if find_element_from_parent(element, 'tweet element', tweet_row_id, By.ID):
        return True
    else:
        return False


def get_latest_tweet_by_viewgroup(driver, except_ids=[]):
    LOGGER.debug('Get latest tweet by ViewGroup other than pinned or promoted tweet')
    all_list_id = 'android:id/list'
    tweet_viewgroup_element_xpath = ('//androidx.recyclerview.widget.RecyclerView'
                                     '[@resource-id="android:id/list"]/android.view.ViewGroup')
    tweet_row_id = 'com.twitter.android:id/row'
    times = 0
    while True:
        random_sleep()
        tweet_viewgroup_elements = driver().find_elements_by_xpath(
            tweet_viewgroup_element_xpath)
        if not tweet_viewgroup_elements:
            LOGGER.error('Cannot find tweet ViewGroup element')
            return None

        element = None
        for tweet_viewgroup_element in tweet_viewgroup_elements:
            if not check_element_is_tweet_element(tweet_viewgroup_element):
                continue

            tweet_element = tweet_viewgroup_element.find_element_by_id(
                tweet_row_id)
            if check_pinned_tweet(tweet_element) or check_promoted_tweet(
                    driver, tweet_element):
                element = tweet_viewgroup_element
                continue

            content = tweet_element.get_attribute('content-desc')
            #  LOGGER.debug(f'content: {content}')
            p = '(.*( \.){2,})'
            m = re.match(p, content, re.MULTILINE | re.DOTALL)
            if m:
                effect_content = m[0]
                if effect_content in except_ids:
                    LOGGER.debug(f'Ignore the element content: {effect_content}')
                    element = tweet_viewgroup_element
                    continue
                else:
                    return tweet_viewgroup_element
            else:
                LOGGER.error('Cannot find effective content')
                #  effect_content = ''

        #  swipe_up(driver)
        #  element = driver().find_element_by_id(
        #          'com.twitter.android:id/outer_layout_row_view_tweet')
        if element:
            swipe_up_element(driver, element, duration=2000)
            #  swipe_up_tweet(driver, element, duration=2000)
        #  swipe_up_half_screen(driver)
        times += 1
        if times > 20:
            LOGGER.error('Some erroe happened, and exit loop')
            break


def click_suggested_follows_close_button(driver):
    suggested_account_dismiss_button_id = 'com.twitter.android:id/dismiss'
    suggested_account_dismiss_button_id1 = 'com.twitter.android:id/dismiss_btn'
    click_element(driver, 'dismiss button',
                  suggested_account_dismiss_button_id, By.ID)  # close suggested panel
    click_element(driver, 'dismiss button',
                  suggested_account_dismiss_button_id1, By.ID)  # close suggested panel


def tap_element(driver, element):
    LOGGER.debug('Tap the element')
    location = element.location
    size = element.size
    x = location['x'] + size['width'] // 2
    y = location['y'] + size['height'] // 2
    driver().tap([(x, y)], duration=1000)


def click_tweet_by_header(driver, tweet_element):
    header_id = 'com.twitter.android:id/tweet_header'
    try:
        driver().find_element_by_id(header_id).click()
        LOGGER.debug('Click the tweet header')
    except Exception as e:
        LOGGER.exception(e)
        tweet_element.click()
        LOGGER.debug('Click the tweet')


def swipe_up_tweet(driver, tweet_element, duration):
    container_id = 'android:id/list'
    header_tab_id = 'com.twitter.android:id/tabs_holder'

    container = driver().find_element_by_id(container_id)
    header = driver().find_element_by_id(header_tab_id)

    container_x = container.location['x']
    container_y = container.location['y'] - header.size['height']
    swipe_up_element(driver, tweet_element, duration=duration, end_y=container_y)


def update_or_create_comment(tweet_object, comment, is_used=False):
    return Comment.objects.update_or_create(tweet=tweet_object,
                                            comment=comment, is_used=is_used)


def update_or_create_comments(tweet_object, comments, is_used=False):
    for comment in comments:
        #  c = Comment(tweet=tweet_object, comment=comment, is_used=is_used)
        #  c.save()
        update_or_create_comment(tweet_object, comment=comment,
                                 is_used=is_used)


def check_comment_exists(comment):
    return Comment.objects.filter(comment=comment, is_used=True).exists()


def get_comment_from_db(tweet, retry_times=3, timeout=120, is_used=True):
    LOGGER.debug('Get comments from DB or API')
    (tweet_object, created) = Tweet.objects.get_or_create(text=tweet)
    get_one_from_api = False
    # this tweet doesn't exist in db, then get comment from API
    if created:
        get_one_from_api = True
    # The tweet existed
    else:
        comments = Comment.objects.filter(tweet=tweet_object, is_used=False)
        # no required comments, then get them from API
        if not comments:
            get_one_from_api = True
        else:
            LOGGER.debug('Get comments from DB')
            #  obj = comments.first()
            obj = random.choice(comments)

            # check comment existence
            if check_comment_exists(obj.comment):
                LOGGER.error(f'This comment existed in DB: {obj.comment}')
                return
            else:
                if is_used:
                    obj.is_used = is_used
                    obj.save()
                return obj.comment

    if get_one_from_api:
        LOGGER.debug('Get comments from API')
        comments = get_comment(tweet, retry_times=retry_times, timeout=timeout,
                               get_one=False)
        if not comments:
            LOGGER.warning(f'Cannot get comments from comment API')
            return
        # save the comments into db
        update_or_create_comments(tweet_object, comments)

        # get random comment
        c = random.choice(comments)

        # check comment existence
        if check_comment_exists(c):
            LOGGER.error(f'This comment existed in DB: {obj.comment}')
            return
        else:
            update_or_create_comment(tweet_object, c, is_used=is_used)
            return c
