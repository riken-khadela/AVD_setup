import random
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from twbot.basebot import BaseBot
from appium.webdriver.common.mobileby import By

from utils import set_log
from conf import PRJ_PATH, LOG_LEVEL, LOG_DIR
from conf import CYBERGHOSTVPN_APK
from accounts_conf import CYBERGHOSTVPN_USERNAME, CYBERGHOSTVPN_PASSWORD

from selenium.webdriver.support import expected_conditions as EC

from utils import random_sleep
from twbot.dialogs import RateDialog, VpnConfirmDialog, MaximumDevicesReachedDialog
from twbot.dialogs import AuthenticationErrorDialog, NewWifiDetectedDialog
from main import LOGGER
from conf import CYBERGHOSTVPN_SERVERS


class CyberGhostVpn(BaseBot):
    app_id = package = "de.mobileconcepts.cyberghost"
    main_activity = ".view.app.AppActivity"
    apk = CYBERGHOSTVPN_APK

    timeout = 5

    username = CYBERGHOSTVPN_USERNAME
    password = CYBERGHOSTVPN_PASSWORD

    activity = ".view.app.AppActivity"
    name = 'First page'

    # page: Your privacy is our goal
    tv_screen_title_id = 'de.mobileconcepts.cyberghost:id/tv_screen_title'
    tv_privacy_content_id = 'de.mobileconcepts.cyberghost:id/tv_privacy_content'
    button_opt_out_id = 'de.mobileconcepts.cyberghost:id/button_opt_out'
    button_agree_id = 'de.mobileconcepts.cyberghost:id/button_agree'

    # page: Create a new account
    tilEmail_id = 'de.mobileconcepts.cyberghost:id/tilEmail'
    email_input_id = 'de.mobileconcepts.cyberghost:id/email_input'
    tilPassword_id = 'de.mobileconcepts.cyberghost:id/tilPassword'
    password_input_id = 'de.mobileconcepts.cyberghost:id/password_input'
    button_sign_up_id = 'de.mobileconcepts.cyberghost:id/button_sign_up'
    button_return_id = 'de.mobileconcepts.cyberghost:id/button_return'
    existing_user_button_id = button_return_id

    # page: Login
    textInputLayout_id = 'de.mobileconcepts.cyberghost:id/textInputLayout'
    login_username_input_id = 'de.mobileconcepts.cyberghost:id/login_username_input'
    textInputLayout2_id = 'de.mobileconcepts.cyberghost:id/textInputLayout2'
    login_password_input_id = 'de.mobileconcepts.cyberghost:id/login_password_input'
    button_login_id = 'de.mobileconcepts.cyberghost:id/button_login'
    button_forgot_password_id = 'de.mobileconcepts.cyberghost:id/button_forgot_password'

    # page: To secure your traffic Ghostie needs to add his VPN magic
    # to your phone settings.
    # Tap the 'OK' button to proceed.
    txtDescription_id = 'de.mobileconcepts.cyberghost:id/txtDescription'
    txtRequestAction_id = 'de.mobileconcepts.cyberghost:id/txtRequestAction'
    btnOk_id = 'de.mobileconcepts.cyberghost:id/btnOk'
    txtFooter_id = 'de.mobileconcepts.cyberghost:id/txtFooter'

    # page: Missing permissions
    # CyberGhost VPN can automatically protect Wi‑Fi networks.
    # To enable this feature, location access is needed.
    # All other CyberGhost VPN features will continue to work,
    # even if you don't grant location permissions.
    tv_screen_description_id = 'de.mobileconcepts.cyberghost:id/tv_screen_description'
    cl_button_one_id = 'de.mobileconcepts.cyberghost:id/cl_button_one'
    btn_settings_location_permission_id = 'de.mobileconcepts.cyberghost:id/btn_settings_location_permission'
    iv_settings_location_permission_id = 'de.mobileconcepts.cyberghost:id/iv_settings_location_permission'
    cl_button_two_id = 'de.mobileconcepts.cyberghost:id/cl_button_two'
    btn_settings_location_service_id = 'de.mobileconcepts.cyberghost:id/btn_settings_location_service'
    iv_settings_location_service_id = 'de.mobileconcepts.cyberghost:id/iv_settings_location_service'
    btnSkip_id = 'de.mobileconcepts.cyberghost:id/btnSkip'

    # page: connect vpn main interface
    # toolbar
    toolbar_id = 'de.mobileconcepts.cyberghost:id/toolbar'
    txtWifi_id = 'de.mobileconcepts.cyberghost:id/txtWifi'
    btn_settings_id = 'de.mobileconcepts.cyberghost:id/btn_settings'
    top_left_corner_id = 'de.mobileconcepts.cyberghost:id/top_left_corner'

    title_text_id = 'de.mobileconcepts.cyberghost:id/title_text'
    connectionButton_id = 'de.mobileconcepts.cyberghost:id/connectionButton'
    button_id = 'de.mobileconcepts.cyberghost:id/button'

    # select location
    control_fragment_container_id = 'de.mobileconcepts.cyberghost:id/control_fragment_container'
    content_id = 'de.mobileconcepts.cyberghost:id/content'
    label_id = 'de.mobileconcepts.cyberghost:id/label'
    location_selection_id = 'de.mobileconcepts.cyberghost:id/location_selection'
    location_icon_id = 'de.mobileconcepts.cyberghost:id/location_icon'
    location_name_id = 'de.mobileconcepts.cyberghost:id/location_name'

    # bottom part
    button_crm_article_id = 'de.mobileconcepts.cyberghost:id/button_crm_article'

    # page: Servers(locations, Countries)
    # toolbar
    btnBack_id = 'de.mobileconcepts.cyberghost:id/btnBack'
    tvToolbarTitle_id = 'de.mobileconcepts.cyberghost:id/tvToolbarTitle'
    btn_search_id = 'de.mobileconcepts.cyberghost:id/btn_search'
    # after clicking search button
    etToolbarSearch_id = 'de.mobileconcepts.cyberghost:id/etToolbarSearch'
    search_input_id = etToolbarSearch_id
    no_items_found_text = 'No items found'

    # tabbar
    flTabLayoutContainer_id = 'de.mobileconcepts.cyberghost:id/flTabLayoutContainer'
    tabLayoutVersion2_id = 'de.mobileconcepts.cyberghost:id/tabLayoutVersion2'
    TAB_COUNTRIES_id = 'de.mobileconcepts.cyberghost:id/TAB_COUNTRIES'
    metaTabSize_id = 'de.mobileconcepts.cyberghost:id/metaTabSize'
    title_id = 'de.mobileconcepts.cyberghost:id/title'
    TAB_STREAMING_id = 'de.mobileconcepts.cyberghost:id/TAB_STREAMING'
    vDividerEnd_id = 'de.mobileconcepts.cyberghost:id/vDividerEnd'
    TAB_FAVORITES_id = 'de.mobileconcepts.cyberghost:id/TAB_FAVORITES'
    vDividerStart_id = 'de.mobileconcepts.cyberghost:id/vDividerStart'

    # server list
    interceptFrameLayout_id = 'de.mobileconcepts.cyberghost:id/interceptFrameLayout'
    swipe_refresh_layout_id = 'de.mobileconcepts.cyberghost:id/swipe_refresh_layout'
    recycler_view_id = 'de.mobileconcepts.cyberghost:id/recycler_view'
    list_root_element_id = recycler_view_id
    item_relative_xpath = '//androidx.recyclerview.widget.RecyclerView'
    item_relative_id = 'de.mobileconcepts.cyberghost:id/content'
    tvTitle_id = 'de.mobileconcepts.cyberghost:id/tvTitle'
    item_title_relative_id = tvTitle_id
    flFavorite_id = 'de.mobileconcepts.cyberghost:id/flFavorite'
    item_favorite_relative_id = flFavorite_id
    btn_add_to_favorite_id = 'de.mobileconcepts.cyberghost:id/btn_add_to_favorite'
    item_favorite_btn_relative_id = btn_add_to_favorite_id
    btnMore_id = 'de.mobileconcepts.cyberghost:id/btnMore'
    item_more_button_relative_id = btnMore_id

    # page: vpn connected
    cl_vpn_location_info_id = 'de.mobileconcepts.cyberghost:id/cl_vpn_location_info'
    location_value_id = 'de.mobileconcepts.cyberghost:id/location_value'
    cl_ip_info_id = 'de.mobileconcepts.cyberghost:id/cl_ip_info'
    value_vpn_ip_info_id = 'de.mobileconcepts.cyberghost:id/value_vpn_ip_info'
    value_local_ip_info_id = 'de.mobileconcepts.cyberghost:id/value_local_ip_info'

    def __init__(self, driver, logger=LOGGER):
        super().__init__(driver)
        self.logger = logger
        self.vpn_confirm_dialog = VpnConfirmDialog(driver)
        self.rate_dialog = RateDialog(driver)
        self.maximum_devices_dialog = MaximumDevicesReachedDialog(driver)
        self.auth_dialog = AuthenticationErrorDialog(driver)
        self.wifi_dialog = NewWifiDetectedDialog(driver)

    @staticmethod
    def get_random_usa_server():
        country = "United States"
        city = random.choice(CYBERGHOSTVPN_SERVERS[country])
        return country, city

    @staticmethod
    def get_server_list():
        return CYBERGHOSTVPN_SERVERS.keys()

    def click_opt_out_button(self):
        return self.click_element('Opt out button', self.button_opt_out_id,
                                  locator_type=By.ID, timeout=self.timeout)

    def click_agree_button(self):
        return self.click_element('Agree&continue button',
                                  self.button_agree_id, locator_type=By.ID, timeout=self.timeout)

    def click_existing_user_button(self):
        return self.click_element('Existing user button',
                                  self.existing_user_button_id, locator_type=By.ID,
                                  timeout=self.timeout)

    def input_username(self):
        return self.input_text(self.username, 'Email/Username input element',
                               self.login_username_input_id, By.ID, timeout=self.timeout)

    def input_password(self):
        return self.input_text(self.password, 'Password input element',
                               self.login_password_input_id, By.ID, timeout=self.timeout)

    def input_search_text(self, text):
        return self.input_text(text, 'Search input element',
                               self.search_input_id, By.ID, timeout=self.timeout)

    def click_login_button(self):
        return self.click_element('Login button', self.button_login_id,
                                  locator_type=By.ID, timeout=self.timeout)

    def click_login_title(self):
        return self.click_element('Login title', self.tv_screen_title_id,
                                  locator_type=By.ID, timeout=self.timeout)

    def click_proceed_ok_button(self):
        return self.click_element('Proceed OK button', self.btnOk_id,
                                  locator_type=By.ID, timeout=self.timeout)

    def click_confirm_dialog_ok_button(self):
        self.vpn_confirm_dialog.click_ok_button()

    def click_missing_permissions_skip_button(self):
        return self.click_element('Missing permissions Skip button',
                                  self.btnSkip_id, locator_type=By.ID, timeout=self.timeout)

    def click_select_location_button(self):
        return self.click_element('Select location button',
                                  self.location_selection_id, locator_type=By.ID,
                                  timeout=self.timeout)

    def click_select_connect_button(self):
        return self.click_element('Vpn Connect button',
                                  self.connectionButton_id, locator_type=By.ID,
                                  timeout=self.timeout)

    def click_search_button(self):
        return self.click_element('Search button',
                                  self.btn_search_id, locator_type=By.ID,
                                  timeout=self.timeout)

    def click_search_button_until_search_input(self, times=5):
        while times > 0:
            self.click_search_button()
            if self.find_element('Search input element', self.search_input_id,
                                 By.ID, timeout=self.timeout):
                return True
            random_sleep(1, 3)
            times -= 1

    def click_streaming_tab(self):
        return self.click_element('Streaming tab',
                                  self.TAB_STREAMING_id, locator_type=By.ID,
                                  timeout=self.timeout)

    def click_countries_tab(self):
        return self.click_element('Countries tab',
                                  self.TAB_COUNTRIES_id, locator_type=By.ID,
                                  timeout=self.timeout)

    def get_countries_in_one_screen(self):
        return self.get_item_contents_from_list(self.list_root_element_id,
                                                self.item_relative_id, self.item_title_relative_id,
                                                root_locator_type=By.ID, item_locator_type=By.ID,
                                                item_content_locator_type=By.ID, timeout=self.timeout)

    def find_title_element_named_country(self, country):
        # wait the title is changed to the country
        return self.find_element(f'Title "{country}" element',
                                 self.tvToolbarTitle_id, locator_type=By.ID,
                                 timeout=self.timeout,
                                 condition_func=EC.text_to_be_present_in_element,
                                 condition_other_args=(country,))

    def find_title_element_named_servers(self):
        # wait the title is changed to 'Servers'
        return self.find_element(f'Title "Servers" element',
                                 self.tvToolbarTitle_id, locator_type=By.ID,
                                 timeout=self.timeout,
                                 condition_func=EC.text_to_be_present_in_element,
                                 condition_other_args=('Servers',))

    def get_servers_in_one_screen(self, checked_countries=[]):
        self.logger.info('Get servers in this screen')
        self.find_title_element_named_servers()  # wait a moment for freshing
        elements = self.get_item_elements_from_list(self.list_root_element_id,
                                                    self.item_relative_id, root_locator_type=By.ID,
                                                    item_locator_type=By.ID, timeout=self.timeout)

        restart_get_elements_flag = False
        servers = {}
        for element in elements:
            country = self.get_text_from_parent(element, 'Country text',
                                                self.item_title_relative_id, locator_type=By.ID)
            if country is None or country in checked_countries:
                continue
            checked_countries.append(country)

            cities = []
            more_element = self.find_element_from_parent(element,
                                                         'More button', self.item_more_button_relative_id,
                                                         locator_type=By.ID)
            if more_element:
                cities = self.get_cities(more_element=more_element,
                                         country=country, go_back=True)
                restart_get_elements_flag = True

            servers[country] = cities
            if restart_get_elements_flag:
                break

        if restart_get_elements_flag:
            servers.update(self.get_servers_in_one_screen(
                checked_countries=checked_countries))

        return servers

    def get_cities_in_one_screen(self, more_element=None, country='',
                                 go_back=False):
        self.logger.debug(f'Get cities in this screen. '
                          f'Has more element: {bool(more_element)}, Go back: {go_back}')
        if more_element:
            more_element.click()
            # wait the title is changed to the country
            self.find_title_element_named_country(country=country)

        items = self.get_item_contents_from_list(
            self.list_root_element_id, self.item_relative_id,
            self.item_title_relative_id, root_locator_type=By.ID,
            item_locator_type=By.ID,
            item_content_locator_type=By.ID, timeout=self.timeout)
        cities = [e.strip() for e in items if e]

        if go_back:
            self.click_go_back_button()
            # wait the title is changed to 'Servers'
            self.find_title_element_named_servers()

        return cities

    def get_cities(self, more_element=None, country='', go_back=False):
        self.logger.info(f'Get all cities')
        cities = []
        cities_in_one_screen = self.get_cities_in_one_screen(
            more_element=more_element, country=country, go_back=False)
        while True:
            # check if it is the last screen
            #  self.logger.debug(f'cities_in_one_screen: {cities_in_one_screen}')
            #  self.logger.debug(f'cities: {cities}')
            if set(cities_in_one_screen) <= set(cities):
                if go_back:
                    self.click_go_back_button()
                return cities
            else:
                cities.extend(cities_in_one_screen)

            # swipe one screen
            elements = self.get_item_elements_from_list(
                self.list_root_element_id, self.item_relative_id,
                root_locator_type=By.ID, item_locator_type=By.ID,
                timeout=self.timeout)
            effective_elements = [e for e in elements if e]
            last_element = effective_elements[-1]
            first_element = effective_elements[0]
            end_y = first_element.location['y']
            self.driver.drag_and_drop(last_element, first_element)

            # get cities again
            cities_in_one_screen = self.get_cities_in_one_screen(
                more_element=None, country='', go_back=False)

    def get_servers(self):
        self.logger.info(f'Get all servers')
        servers = {}
        while True:
            servers_in_one_screen = self.get_servers_in_one_screen()
            # check if it is the last screen
            if set(servers_in_one_screen) <= set(servers):
                return servers
            else:
                servers.update(servers_in_one_screen)

            # swipe one screen
            elements = self.get_item_elements_from_list(
                self.list_root_element_id, self.item_relative_id,
                root_locator_type=By.ID, item_locator_type=By.ID,
                timeout=self.timeout)
            effective_elements = [e for e in elements if e]
            last_element = effective_elements[-1]
            first_element = effective_elements[0]
            end_y = first_element.location['y']
            self.driver.drag_and_drop(last_element, first_element)

    def get_list_elements(self):
        return self.get_item_elements_from_list(
            self.list_root_element_id, self.item_relative_id,
            root_locator_type=By.ID, item_locator_type=By.ID,
            timeout=self.timeout)

    def select_server(self, country='', city='', random_max_num=15):
        self.find_title_element_named_servers()  # wait a moment for freshing
        random_sleep()

        # random scroll screen
        origin_country = country
        if origin_country == '':
            random_times = random.randint(0, random_max_num)
            LOGGER.debug(f'random_times: {random_times}')

        country_compared_flag = False
        countries = []
        while True:
            elements = self.get_item_elements_from_list(
                self.list_root_element_id, self.item_relative_id,
                root_locator_type=By.ID, item_locator_type=By.ID,
                timeout=self.timeout)

            # get a country randomly
            if origin_country == '' and random_times <= 0:
                while True:
                    element = random.choice([e for e in elements if e])
                    country = self.get_text_from_parent(element, 'Country text',
                                                        self.item_title_relative_id, locator_type=By.ID)
                    self.logger.debug(f'Random country: {country}')
                    if country:
                        break

            countries_in_one_screen = []
            for element in elements:
                element_country = self.get_text_from_parent(element,
                                                            'Country text', self.item_title_relative_id,
                                                            locator_type=By.ID)
                if element_country is None:
                    continue
                countries_in_one_screen.append(element_country)

                # select the server
                # country is compared, then compare the city
                if element_country.strip().lower() == country.strip().lower():
                    more_element = self.find_element_from_parent(element,
                                                                 'More button', self.item_more_button_relative_id,
                                                                 locator_type=By.ID)
                    if more_element:
                        return self.select_city(city, more_element=more_element,
                                                country=country)

                    element.click()
                    return True

            # check if it is the last screen
            if set(countries_in_one_screen) <= set(countries):
                self.logger.debug('This is last screen, now exit loop')
                break
            countries.extend(countries_in_one_screen)
            #  self.logger.debug(f'countries_in_one_screen: {countries_in_one_screen}')
            #  self.logger.debug(f'countries: {countries}')

            if origin_country == '':
                random_times -= 1

            # scroll screen
            self.scroll_last_element_to_first_from_list(elements)

        # Cannot get one country randomly, then select one from last screen
        if origin_country == '':
            random_sleep()
            elements = self.get_item_elements_from_list(
                self.list_root_element_id, self.item_relative_id,
                root_locator_type=By.ID, item_locator_type=By.ID,
                timeout=self.timeout)
            self.logger.debug('Select the random country from the last screen')
            #  self.logger.debug(elements)
            while True:
                element = random.choice([e for e in elements if e])
                try:
                    country = self.get_text_from_parent(element,
                                                        'Country text', self.item_title_relative_id,
                                                        locator_type=By.ID)
                    if country is None:
                        continue
                    self.logger.info(f'Random country: {country}')

                    element.click()
                    return True
                except Exception as e:
                    self.logger.error(e)
                    continue

        return False

    def select_city(self, city='', more_element=None, country='',
                    random_max_num=3):
        self.logger.debug(f'Select the city "{city}". '
                          f'Has more element: {bool(more_element)}')
        if more_element:
            more_element.click()
            # wait the title is changed to the country
            self.find_title_element_named_country(country=country)

        random_sleep()
        # random scroll screen
        origin_city = city
        if origin_city == '':
            random_times = random.randint(0, random_max_num)
            LOGGER.debug(f'random_times: {random_times}')

        cities = []
        while True:
            elements = self.get_item_elements_from_list(
                self.list_root_element_id, self.item_relative_id,
                root_locator_type=By.ID, item_locator_type=By.ID,
                timeout=self.timeout)

            # get a city randomly
            if origin_city == '' and random_times <= 0:
                while True:
                    element = random.choice([e for e in elements if e])
                    city = self.get_text_from_parent(element, 'City text',
                                                     self.item_title_relative_id, locator_type=By.ID)
                    self.logger.debug(f'Random city: {city}')
                    if city:
                        break

            cities_in_one_screen = []
            for element in elements:
                element_city = self.get_text_from_parent(element, 'City text',
                                                         self.item_title_relative_id, locator_type=By.ID)
                if element_city is None:
                    continue
                cities_in_one_screen.append(element_city)

                # select the server
                if element_city.strip().lower() == city.strip().lower():
                    element.click()
                    return True

            # check if it is the last screen
            if set(cities_in_one_screen) <= set(cities):
                self.logger.debug('This is last screen, now exit loop')
                break
            cities.extend(cities_in_one_screen)

            if origin_city == '':
                random_times -= 1

            # scroll screen
            self.scroll_last_element_to_first_from_list(elements)

        # Cannot get one city randomly, then select one from last screen
        if origin_city == '':
            random_sleep()
            elements = self.get_item_elements_from_list(
                self.list_root_element_id, self.item_relative_id,
                root_locator_type=By.ID, item_locator_type=By.ID,
                timeout=self.timeout)
            self.logger.debug('Select the random city from the last screen')
            while True:
                element = random.choice([e for e in elements if e])
                city = self.get_text_from_parent(element, 'City text',
                                                 self.item_title_relative_id, locator_type=By.ID)
                if city is None:
                    continue
                self.logger.debug(f'Random city: {city}')

                try:
                    element.click()
                    return True
                except Exception as e:
                    self.logger.error(e)
                    continue

        return False

    def is_connected(self, timeout=None):
        if timeout is None:
            timeout = self.timeout
        self.logger.info(f'Checking if the VPN is connected. '
                         f'Timeout: {timeout}')

        element = self.find_element('Vpn location', self.location_value_id,
                                    locator_type=By.ID, page='Main page', timeout=timeout)
        if element:
            self.logger.info(f'Vpn is connected to: {element.text}')
            return True

    def is_main_page(self):
        element = self.find_element('Connection button',
                                    self.connectionButton_id, locator_type=By.ID, page='Main page',
                                    timeout=self.timeout)
        #  timeout=0)
        if element:
            self.logger.info(f'In the main page')
            return True

    def is_login_page(self):
        element = self.find_element('Login button',
                                    self.button_login_id, locator_type=By.ID, page='Login page',
                                    timeout=self.timeout)
        if element:
            self.logger.info(f'In the login page')
            return True

    def click_go_back_button(self):
        return self.click_element('Go back button', self.btnBack_id,
                                  locator_type=By.ID, timeout=self.timeout)

    def start_ui(self, reconnect=True, country='', city='', retry_times=3,
                 check_connect_timeout=30, find_method='search'):
        """User interface for starting vpn

        find_method: search or scroll
        """
        while retry_times > 0:
            try:
                if not self.is_app_installed():
                    reconnect = True

                if reconnect:
                    self.install()
                    self.start()
                    self.driver.wait_activity(activity=self.activity,
                                              timeout=check_connect_timeout // 2)
                else:
                    try:
                        self.logger.info(f'Activate the app and check '
                                         'the connection')
                        self.driver.activate_app(self.app_id)
                        if self.is_connected(timeout=check_connect_timeout // 2):
                            return True
                        reconnect = True
                    except Exception as e:
                        self.logger.error(e)
                        reconnect = True
                        continue
                random_sleep(5,8)
                self.check_service_not_reachable()
                if self.is_login_page():
                    self.input_username()
                    self.input_password()
                    self.click_login_title()
                    self.click_login_button()
                    random_sleep(1, 3)
                    if self.maximum_devices_dialog.exists():
                        self.maximum_devices_dialog.click_remove_all_devices_button()
                        self.click_login_button()
                    self.click_proceed_ok_button()
                    # check the vpn connection dialog
                    if self.vpn_confirm_dialog.exists():
                        self.click_confirm_dialog_ok_button()
                    #  self.click_confirm_dialog_ok_button()
                    self.click_missing_permissions_skip_button()
                # If the first screen is not main page, then setup the vpn 
                elif not self.is_main_page():
                    self.click_opt_out_button()
                    self.click_existing_user_button()
                    random_sleep(2, 3)
                    self.input_username()
                    self.input_password()
                    self.click_login_title()
                    self.click_login_button()
                    random_sleep(1, 3)
                    if self.maximum_devices_dialog.exists():
                        self.maximum_devices_dialog.click_remove_all_devices_button()
                        self.click_login_button()
                    self.click_proceed_ok_button()
                    # check the vpn connection dialog
                    if self.vpn_confirm_dialog.exists():
                        self.click_confirm_dialog_ok_button()
                    #  self.click_confirm_dialog_ok_button()
                    self.click_missing_permissions_skip_button()

                # after setup, then go to the main page.
                if self.is_main_page():
                    self.click_select_location_button()
                    if find_method == 'search':
                        self.click_search_button_until_search_input()
                        self.select_server_by_search(country=country, city=city)
                    else:
                        self.select_server(country=country, city=city)

                    # check the vpn connection dialog
                    if self.vpn_confirm_dialog.exists():
                        self.click_confirm_dialog_ok_button()
                else:  # may be there are some other popups
                    if self.handle_popups():
                        continue

                # after selecting ther server, it will connect automatically
                if self.is_connected(timeout=check_connect_timeout):
                    return True

                # if it doesn't connect automatically, then press the connect button
                if self.is_main_page():
                    self.click_select_connect_button()
                    # check the vpn connection dialog
                    if self.vpn_confirm_dialog.exists():
                        self.click_confirm_dialog_ok_button()
                    if self.is_connected(timeout=check_connect_timeout):
                        return True
                else:  # may be there are some other popups
                    if self.handle_popups():
                        continue
            except Exception as e:
                self.logger.error(e)

            retry_times -= 1
            self.logger.info(f'Retry to connect again')

    def handle_popups(self):
        if self.maximum_devices_dialog.exists():
            self.maximum_devices_dialog.click_remove_all_devices_button()
            self.click_login_button()
            return True

        # check the rate dialog
        if self.rate_dialog.exists():
            self.rate_dialog.click_not_now_button()
            return True

        # check the vpn connection dialog
        if self.vpn_confirm_dialog.exists():
            self.click_confirm_dialog_ok_button()
            return True

        if self.auth_dialog.exists():
            self.auth_dialog.click_ok_button()
            return True

        if self.wifi_dialog.exists():
            self.wifi_dialog.click_ignore_button()
            return True

    def select_server_by_search(self, country='', city=''):
        if country and city:
            self.logger.info(f'Search country "{country}" and city "{city}"')
        elif country:
            self.logger.info(f'Search country "{country}"')
        else:
            country = random.choice([k for k in CYBERGHOSTVPN_SERVERS])
            self.logger.info(f'Search random country "{country}"')

        if not city:
            cities = CYBERGHOSTVPN_SERVERS.get(country, [])
            if cities:
                city = random.choice(cities)
                self.logger.info(f'Search random city "{city}"')
            else:
                city = ''

        self.find_element('Search input element', self.search_input_id,
                          By.ID, timeout=self.timeout)  # wait for refreshing
        original_elements = self.get_list_elements()
        original_num = len(original_elements)
        self.logger.debug(f'Number of original elements: {original_num}')
        # search country
        self.input_search_text(country)
        random_sleep(1, 3)

        result_elements = self.get_list_elements()
        result_num = len(result_elements)
        self.logger.debug(f'Number of result elements: {result_num}')
        #  if result_num == original_num:  # wait for changing result
        #      random_sleep(1, 3)

        # check the result
        for element in result_elements:
            element_country = self.get_text_from_parent(element,
                                                        'Country text', self.item_title_relative_id,
                                                        locator_type=By.ID)
            if element_country is None:
                continue
            if element_country == self.no_items_found_text:
                self.logger.info(self.no_items_found_text)
                return False
            if element_country == country:
                self.logger.debug(f'Found the country: {country}')
                if not city:
                    self.logger.debug(f'Click the country element')
                    element.click()
                    return True
                # select city
                more_element = self.find_element_from_parent(element,
                                                             'More button', self.item_more_button_relative_id,
                                                             locator_type=By.ID)
                if more_element:
                    more_element.click()
                    random_sleep(1, 3)
                    return self.select_city_by_search(city)

    def select_city_by_search(self, city=''):
        self.logger.debug(f'Select the city "{city}"')

        original_elements = self.get_list_elements()
        original_num = len(original_elements)
        self.logger.debug(f'Number of original elements: {original_num}')

        if not city:
            element = random.choice(original_elements)
            element_city = self.get_text_from_parent(element, 'City text',
                                                     self.item_title_relative_id, locator_type=By.ID)
            self.logger.debug('Select random city "{element_city}"')
            element.click()
            return True

        # search city
        self.input_search_text(city)
        random_sleep(1, 3)

        result_elements = self.get_list_elements()
        result_num = len(result_elements)
        self.logger.debug(f'Number of result elements: {result_num}')
        #  if result_num == original_num:  # wait for changing result
        #      random_sleep(1, 3)

        cities = []
        while True:
            cities_in_one_screen = []
            for element in result_elements:
                element_city = self.get_text_from_parent(element, 'City text',
                                                         self.item_title_relative_id, locator_type=By.ID)
                if element_city is None:
                    continue
                cities_in_one_screen.append(element_city)

                if element_city == city:
                    element.click()
                    return True

                if element_city == self.no_items_found_text:
                    self.logger.info(self.no_items_found_text)
                    return False

            # check if it is the last screen
            if set(cities_in_one_screen) <= set(cities):
                self.logger.debug('This is last screen, now exit loop')
                break
            cities.extend(cities_in_one_screen)

            # scroll screen
            self.scroll_last_element_to_first_from_list(result_elements)

    def check_service_not_reachable(self):
        text1 = "Service not reachable"
        text2 = "No Network"
        service_not_reachable = self.find_elements_by_text(text1)
        no_network = self.find_elements_by_text(text2)
        if service_not_reachable or no_network:
            self.disable_aeroplane_mode()

    def find_elements_by_text(self, text):
        return self.driver.find_elements_by_android_uiautomator(f"new UiSelector().text(\"{text}\")")

    def disable_aeroplane_mode(self):
        self.driver.start_activity("com.android.settings", ".Settings$NetworkDashboardActivity")
        self.wait_for_activity(".Settings$NetworkDashboardActivity")
        time.sleep(2)
        aeroplane_mode_switch = self.driver.find_elements(By.ID, 'android:id/switch_widget')
        if aeroplane_mode_switch:
            if aeroplane_mode_switch[0].get_attribute("checked") == "true":
                aeroplane_mode_switch[0].click()

    def wait_for_activity(self, activity, timeout=20, interval=1):
        try:
            WebDriverWait(self.driver, timeout, interval).until(
                lambda d: d.current_activity == activity
            )
            return True
        except TimeoutException:
            return False
