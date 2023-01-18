import re
import types

from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from main import LOGGER
from utils import get_absolute_path_str


class AndroidBaseBot:
    """Base user interface level API for bot on android"""
    timeout = 5

    apk = ''
    app_id = package = ''
    main_activity = ''

    activity = ''
    name = ''

    def __init__(self, driver, logger=LOGGER, timeout=timeout):
        self.old_driver = driver
        self.driver = BaseBot.get_real_driver(driver)
        self.wait_obj = WebDriverWait(self.driver, self.timeout)
        self.logger = logger
        self.timeout = timeout

    @staticmethod
    def get_real_driver(driver):
        if isinstance(driver, WebDriver):
            return driver
        elif isinstance(driver, types.FunctionType) or isinstance(
                driver, types.MethodType):
            return driver()
        else:
            LOGGER.error('Wrong type of driver')

    def start(self, **opts):
        try:
            self.logger.info(f'Start package "{self.package}" with main '
                             f'activity "{self.main_activity}"')
            self.driver.start_activity(self.package, self.main_activity, **opts)
            return True
        except Exception as e:
            self.logger.error(e)
        return False

    def install(self, apk_file='', force=False, **options):
        if not apk_file:
            apk_file = self.apk
        apk_file = get_absolute_path_str(apk_file)

        if not force:
            if self.is_app_installed():
                self.logger.info(
                    f'App "{self.app_id}" has been installed already')
                return True
        try:
            self.logger.info(f'Install APP "{apk_file}" on the device')
            self.driver.install_app(apk_file, **options)
            return True
        except Exception as e:
            self.logger.error(e)
        return False

    def uninstall(self):
        try:
            self.logger.info(f'Uninstall APP "{self.app_id}"')
            self.driver.remove_app(self.app_id)
            return True
        except Exception as e:
            self.logger.error(e)
        return False

    def is_app_installed(self):
        return self.driver.is_app_installed(self.app_id)

    def terminate_app(self):
        return self.driver.terminate_app(self.app_id)

    def find_element(self, element, locator, locator_type=By.XPATH,
                     page=None, timeout=timeout,
                     condition_func=EC.presence_of_element_located,
                     condition_other_args=tuple()):
        """Find an element, then return it or None.

        If timeout is less than or requal zero, then just find.
        If it is more than zero, then wait for the element present.
        """
        try:
            if timeout > 0:
                wait_obj = WebDriverWait(self.driver, timeout)
                #  ele = wait_obj.until(
                #          EC.presence_of_element_located(
                #              (locator_type, locator)))
                ele = wait_obj.until(
                    condition_func((locator_type, locator),
                                   *condition_other_args))
            else:
                #  self.logger.debug(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver.find_element(by=locator_type,
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
                      timeout=timeout):
        """Find an element, then click and return it, or return None"""
        ele = self.find_element(element, locator, locator_type, timeout=timeout)
        if ele:
            ele.click()
            LOGGER.debug(f'Clicked the element: {element}')
            return ele

    def input_text(self, text, element, locator, locator_type=By.XPATH,
                   timeout=timeout, hide_keyboard=True):
        """Find an element, then input text and return it, or return None"""
        if hide_keyboard and self.driver.is_keyboard_shown():
            self.logger.debug(f'Hide keyboard')
            self.driver.hide_keyboard()

        ele = self.find_element(element, locator, locator_type=locator_type,
                                timeout=timeout)
        if ele:
            ele.send_keys(text)
            self.logger.debug(f'Inputed "{text}" for the element: {element}')
            return ele

    def find_page(self, page, element, locator, locator_type=By.XPATH,
                  timeout=timeout):
        """Find en element of a page, then return it or return None"""
        return self.find_element(element, locator, locator_type, page, timeout)

    def swipe_element_vertically(self, element, swipe_from='bottom', times=1,
                                 duration=5000, delta=20, end_y=None, x_delta=50):
        """Swipe up/down the bottom/top of an element to the top/bottom of it
        or other location.
        """
        location = element.location
        size = element.size
        swipe_from = swipe_from.strip().lower()

        start_x = location['x'] + size['width'] // 2
        if swipe_from == 'bottom':
            start_y = location['y'] + size['height']
        else:
            start_y = location['y']

        end_x = start_x
        if not end_y:
            if swipe_from == 'bottom':
                end_y = location['y']
            else:
                end_y = location['y'] + size['height']

        while times > 0:
            LOGGER.debug(f'start_x: {start_x}, start_y: {start_y},'
                         f' end_x: {end_x}, end_y: {end_y}, delta: {delta}')
            if start_y == end_y:
                self.logger.info(
                    f'No neccessary to swipe because of equal end point')
                return
            try:
                #  self.driver.swipe(start_x, start_y, end_x, end_y, duration)
                if swipe_from == 'bottom':
                    self.driver.swipe(start_x - x_delta, start_y - delta,
                                      end_x - x_delta, end_y + delta, duration)
                else:
                    self.driver.swipe(start_x - x_delta, start_y + delta,
                                      end_x - x_delta, end_y - delta, duration)
            except InvalidElementStateException as e:
                LOGGER.error(e)
                if swipe_from == 'bottom':
                    LOGGER.debug(f'Decrease the start_y by delta: {delta}')
                    self.driver.swipe(start_x - x_delta, start_y - delta, end_x - x_delta, end_y,
                                      duration)
                else:
                    LOGGER.debug(f'Increase the start_y by delta: {delta}')
                    self.driver.swipe(start_x - x_delta, start_y + delta, end_x - x_delta, end_y,
                                      duration)
            times -= 1

    def find_element_from_parent(self, parent_element, element, locator,
                                 locator_type=By.XPATH):
        """Find child element from parent, then return it or None"""
        try:
            ele = parent_element.find_element(by=locator_type, value=locator)
            LOGGER.debug(f'Found the element "{element}" from parent')
            return ele
        except NoSuchElementException as e:
            LOGGER.debug(f'Cannot find the element "{element}" from parent')

    def find_elements_from_parent(self, parent_element, element, locator,
                                  locator_type=By.XPATH):
        """Find child elements from parent, then return it or None"""
        try:
            eles = parent_element.find_elements(by=locator_type, value=locator)
            LOGGER.debug(f'Found the elements "{element}" from parent')
            return eles
        except NoSuchElementException as e:
            LOGGER.debug(f'Cannot find the elements "{element}" from parent')

    def get_item_elements_from_list(self, root_locator, item_relative_locator,
                                    root_locator_type=By.XPATH, item_locator_type=By.XPATH,
                                    timeout=timeout):
        root_element = self.find_element('List root element', root_locator,
                                         locator_type=root_locator_type, timeout=timeout)
        if root_element:
            elements = self.find_elements_from_parent(root_element,
                                                      'Item element', item_relative_locator,
                                                      locator_type=item_locator_type)
            if elements:
                return elements

        return tuple()

    def get_item_contents_from_list(self, root_locator, item_relative_locator,
                                    item_content_relative_locatior, root_locator_type=By.XPATH,
                                    item_locator_type=By.XPATH, item_content_locator_type=By.XPATH,
                                    timeout=timeout):
        item_elements = self.get_item_elements_from_list(root_locator,
                                                         item_relative_locator, root_locator_type=root_locator_type,
                                                         item_locator_type=item_locator_type, timeout=timeout)
        contents = []
        for element in item_elements:
            text = self.get_text_from_parent(element, 'Item of list',
                                             item_content_relative_locatior,
                                             locator_type=item_content_locator_type)
            contents.append(text)

        return contents

    def get_activity(self):
        LOGGER.debug(f'Current activity: {self.driver.current_activity}')
        return self.driver.current_activity

    def get_current_activity(self):
        return self.get_activity()

    def element_part_is_in_view_window(self, element, view_window_element):
        LOGGER.debug(f'element rect: {element.rect}')
        LOGGER.debug(f'view_window_element rect: {view_window_element.rect}')
        element_x = element.rect['x']
        element_y = element.rect['y']
        element_width = element.rect['width']
        element_height = element.rect['height']

        view_x = view_window_element.rect['x']
        view_y = view_window_element.rect['y']
        view_width = view_window_element.rect['width']
        view_height = view_window_element.rect['height']

        element_other_x = element_x
        element_other_y = element_y + element_height

        if (element_x >= view_x) and (element_x <= (view_x + view_width)):
            if (element_y >= view_y) and (element_y <= (view_y + view_height)):
                return True

        if (element_other_x >= view_x) and (
                element_other_x <= (view_x + view_width)):
            if (element_other_y >= view_y) and (
                    element_other_y <= (view_y + view_height)):
                return True

        return False

    def check_pattern_in_page_source(self, pattern):
        if re.search(pattern, self.driver.page_source, re.MULTILINE | re.DOTALL):
            return True

    def get_text(self, element, locator, locator_type=By.XPATH,
                 timeout=timeout):
        element = self.find_element(element, locator,
                                    locator_type=locator_type, timeout=timeout)
        if element:
            return element.text

    def get_text_from_parent(self, parent_element, element, locator,
                             locator_type=By.XPATH):
        element = self.find_element_from_parent(parent_element, element,
                                                locator, locator_type=locator_type)
        if element:
            return element.text

    def scroll_element_to_another(self, original_element, destination_element):
        try:
            #  self.driver.drag_and_drop(original_element, destination_element)
            end_y = destination_element.location['y']
            self.swipe_element_vertically(original_element, end_y=end_y)
            return True
        except Exception as e:
            self.logger.debug(e)
        return False

    def scroll_last_element_to_first_from_list(self, elements):
        effective_elements = [e for e in elements if e]
        last_element = effective_elements[-1]
        first_element = effective_elements[0]
        self.scroll_element_to_another(last_element, first_element)

    def emulate_old_driver(self):
        def driver():
            return self.driver

        return driver


BaseBot = AndroidBaseBot
