from src.testlib.selenium.locators.csp import iam_oauth_apps_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class OauthAppsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.iam_oauth_apps_locators = iam_oauth_apps_page.IdentityAndAccessOauthAppsLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_oauth_app_page(self):
        groups_page_link = self.find_element(self.iam_oauth_apps_locators.NAV_OAUTH_APPS)
        if groups_page_link:
            groups_page_link.click()
            self.wait_for_element(self.iam_oauth_apps_locators.TXT_OAUTH_APPS)
            assert self.find_element(self.iam_oauth_apps_locators.TXT_OAUTH_APPS).text == "OAuth Apps", "OAuth Apps page is not working as expected"
            
            assert self.if_element_exists(
                self.iam_oauth_apps_locators.BTN_ADD_APP
            ), "could not find add a user locator={}".format(self.iam_oauth_apps_locators.BTN_ADD_APP)

        else:
            mylog.error(
                "Groups page could not be located using locator={}".format(
                    self.iam_oauth_apps_locators.NAV_PENDING_INVITATIONS
                )
            )
