"""
Inspector module check twitter user accounts information.

Inspector module consist of InspectTwitterAccount class which provides
methods for checking twitter accounts status[active , temporary banned, suspended,]
also keep track of followers and following of active users.

Author : Raj Pardesi
"""
import os.path

from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from tqdm import tqdm

from surviral_avd.settings import BASE_DIR
from twbot.models import TwitterAccount
from webdriver_manager.utils import ChromeType
from main import LOGGER
from utils import run_cmd


class InspectTwitterAccount:
    """InspectTwitterAccount contains methods for performing inspections."""

    def __init__(self, gui=False):
        """Initialize all the objects needed."""
        self.info = {}
        self.active = []
        self.suspended = []
        self.temporary_ban = []
        self.not_exist = []
        self.error_list = []
        self.gui = gui
        self.driver = self.get_driver()
        self.soup = None

    def get_driver(self):
        """loads web drivers for selenium"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--enable-javascript")
        if not self.gui:
            chrome_options.add_argument("--headless")

        chrome_type = None
        result = run_cmd('which google-chrome google-chrome-stable')
        if result:
            (returncode, output) = result
            if returncode == 0:
                chrome_type = ChromeType.GOOGLE

        if not chrome_type:
            result = run_cmd('which chromium')
            if result:
                (returncode, output) = result
                if returncode == 0:
                    chrome_type = ChromeType.CHROMIUM

        if chrome_type:
            driver = webdriver.Chrome(
                    ChromeDriverManager(chrome_type=chrome_type).install(),
                    options=chrome_options)
        else:
            driver = webdriver.Chrome(ChromeDriverManager().install(),
                    options=chrome_options)
        return driver

    def get_profile_names(self):
        """get_profile_names collects and returns list of active accounts username."""
        tws = TwitterAccount.objects.filter().exclude(status="SUSPENDED")
        user_names = [f"{ta.screen_name}" for ta in tws]
        LOGGER.debug(f'user_names: {user_names}')
        return user_names

    def _is_active(self, user_name):
        """Checks for active account."""
        followers = self.soup.find_all("a", {"href": f"/{user_name}/followers"})
        following = self.soup.find_all("a", {"href": f"/{user_name}/following"})

        if followers and following:
            self.info[user_name]["following"] = following[0].text.split(" ")[0]
            self.info[user_name]["followers"] = followers[0].text.split(" ")[0]
            self.active.append(user_name)
            self.info[user_name]["status"] = "active"
            tws = TwitterAccount.objects.filter(screen_name=user_name).first()
            tws.status = "ACTIVE"
            tws.save()
            return True
        return False

    def _is_temporary_ban(self, user_name):
        """Checks  temporary banned account."""
        temporary_ban = self.soup.find_all(
            "span", string="Caution: This account is temporarily restricted"
        )
        if temporary_ban:
            self.temporary_ban.append(user_name)
            self.info[user_name]["status"] = "temporary_ban"
            tws = TwitterAccount.objects.filter(screen_name=user_name).first()
            tws.status = "BANNED"
            tws.save()
            return True
        return False

    def _is_suspended(self, user_name):
        """Checks for suspended account."""
        suspended = self.soup.find("span", string="Account suspended")
        if suspended:
            self.suspended.append(user_name)
            self.info[user_name]["status"] = "suspended"
            tws = TwitterAccount.objects.filter(screen_name=user_name).first()
            tws.status = "SUSPENDED"
            tws.save()
            return True
        return False

    def _is_not_exist(self, user_name):
        """Checks for not existing account."""
        not_exist = self.soup.find(string="This account doesn’t exist")
        if not_exist:
            self.not_exist.append(user_name)
            self.info[user_name]["status"] = "not_exist"
            tws = TwitterAccount.objects.filter(screen_name=user_name).first()
            tws.status = "SUSPENDED"
            tws.save()
            return True

        return False

    def inspect(self, user_names):
        """inspect methods itererate over usernames inspects status.

        Args:
            user_names (list[str]): a list of username to be inspected.
        """

        for user_name in tqdm(user_names):
            self.info[user_name] = {}
            self.driver.get(f"https://twitter.com/{user_name}")
            time.sleep(4)
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

            if self._is_not_exist(user_name):
                continue
            elif self._is_active(user_name):
                continue
            elif self._is_temporary_ban(user_name):
                continue
            elif self._is_suspended(user_name):
                continue

        self.driver.close()
        print(f"INFO : inspected {len(user_names)} twitter accounts.\n")


if __name__ == "__main__":
    # example USE CASse.
    profiles = [
        "Annabel75349496",
        "MckeanAshur",
    ]
    ita = InspectTwitterAccount()
    # ita.inspect(profiles)
