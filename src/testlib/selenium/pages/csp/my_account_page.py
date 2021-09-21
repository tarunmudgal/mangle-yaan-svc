from selenium.webdriver.support.ui import Select

from src.testlib.selenium.locators.csp import login_page, my_account_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class MyAccountPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.my_account_locators = my_account_page.MyAccountLocators
        self.login_page_locators = login_page.LoginPageLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_my_account_page(self):
        assert self.if_element_exists(
            self.login_page_locators.BTN_USER_MENU
        ), "could not find user menu button locator={}".format(self.locators.TB_EMAIL)

        self.click(self.login_page_locators.BTN_USER_MENU)
        self.click(self.my_account_locators.BTN_MY_ACCOUNT)

        self.wait_for_element(self.my_account_locators.TXT_MY_ACCOUNT_TITLE)
        self.find_element(self.my_account_locators.TXT_MY_ACCOUNT_TITLE)
        mylog.debug("My Account page loaded successfully")

    def update_language_preference(self, new_language_name):
        self.click(self.my_account_locators.BTN_PREFERENCES_TAB)
        self.click(self.my_account_locators.BTN_PREFERENCES_LANGUAGE_EDIT)
        language_drop_down = Select(self.find_element(self.my_account_locators.DROP_DOWN_LANGUAGE))
        old_language_name = language_drop_down.first_selected_option.text
        language_drop_down.select_by_visible_text(new_language_name)
        self.click(self.my_account_locators.BTN_PREFERENCES_LANGUAGE_SAVE)

        self.wait_for_spinner_to_disappear(timeout_to_appear=60, timeout_to_disappear=120)
        self.wait_for_element(self.my_account_locators.BTN_PREFERENCES_LANGUAGE_EDIT, timeout=120)
        self.click(self.my_account_locators.BTN_PREFERENCES_LANGUAGE_EDIT)
        language_drop_down = Select(self.find_element(self.my_account_locators.DROP_DOWN_LANGUAGE))
        language_drop_down.select_by_visible_text(old_language_name)
        self.click(self.my_account_locators.BTN_PREFERENCES_LANGUAGE_SAVE)

        self.wait_for_element(self.my_account_locators.BTN_PREFERENCES_LANGUAGE_EDIT, timeout=120)
        self.wait_for_element(self.my_account_locators.TXT_MY_ACCOUNT_TITLE)
        mylog.debug("My Account language preference updated successfully")

        # my_account_page_link = self.find_element(self.my_account_locators.NAV_OAUTH_APPS)
        # if my_account_page_link:
        #     my_account_page_link.click()
        #     self.wait_for_element(self.my_account_locators.TXT_OAUTH_APPS)
        #     assert (
        #             self.find_element(self.my_account_locators.TXT_OAUTH_APPS).text == "OAuth Apps"
        #     ), "OAuth Apps page is not working as expected"
        #
        #     self.verify_page_loaded_correctly_when_commerce_down()
        #
        # else:
        #     mylog.error(
        #         "oAuth Apps page could not be located using locator={}".format(
        #             self.my_account_locators.NAV_PENDING_INVITATIONS
        #         )
        #     )
