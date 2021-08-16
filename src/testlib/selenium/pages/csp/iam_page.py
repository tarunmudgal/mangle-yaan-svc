

from src.testlib.selenium.locators.csp import iam_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class ActiveUsersPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.iam_locators = iam_page.IdentityAndAccessLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_active_users(self):
        users_element = self.find_element(self.iam_locators.IAM)
        if users_element:
            users_element.click()
            active_users = self.find_element(self.iam_locators.Active_users)
            if active_users:
                active_users.click()
                return self.find_element(self.iam_locators.Active_users_text).text
            else:
                print("active users element not found")
        
        return None


    