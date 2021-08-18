from src.testlib.selenium.locators.csp import iam_active_users_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class ActiveUsersPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.iam_locators = iam_active_users_page.IdentityAndAccessLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_active_users(self):
        indentity_access_management_btn = self.find_element(
            self.iam_locators.BTN_IDENTITY_AND_ACCESS_MANAGEMENT
        )
        if indentity_access_management_btn:
            indentity_access_management_btn.click()
            active_users_page_link = self.find_element(self.iam_locators.NAV_ACTIVE_USERS)
            if active_users_page_link:
                active_users_page_link.click()
                self.wait_for_element(self.iam_locators.TXT_ACTIVE_USERS)
                assert self.find_element(self.iam_locators.TXT_ACTIVE_USERS).text == "Active Users", "Active users page is not working as expected"
                assert self.if_element_exists(
                    self.iam_locators.NAV_ACTIVE_USERS_SEARCH
                ), "could not find active users search locator={}".format(self.iam_locators.NAV_ACTIVE_USERS_SEARCH)
                assert self.if_element_exists(
                    self.iam_locators.BTN_ADD_USER
                ), "could not find add user locator={}".format(self.iam_locators.BTN_ADD_USER)

            else:
                mylog.error(
                    "Active Users page could not be located using locator={}".format(
                        self.iam_locators.NAV_ACTIVE_USERS
                    )
                )
