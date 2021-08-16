

from src.testlib.selenium.locators.csp import iam_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class ActiveUsersPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.iam_locators = iam_page.IdentityAndAccessLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_active_users(self):
        print("current_url : ",self.current_url)
        if not self.find_element(self.iam_locators.Active_users):
            print("Active users element not found")
        print("Active users elemnet found")
        self.find_element(self.iam_locators.Active_users).click()
