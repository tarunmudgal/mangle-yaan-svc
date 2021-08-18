from src.testlib.selenium.locators.csp import bs_overview_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class OverviewPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_overview_locators = bs_overview_page.CommerceOverviewLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_overview_page(self):
        billing_subscriptions_btn = self.find_element(
            self.commerce_overview_locators.BTN_BILLING_AND_SUBSCRIPTIONS
        )
        if billing_subscriptions_btn:
            billing_subscriptions_btn.click()
            subscriptions_page_link = self.find_element(self.commerce_overview_locators.NAV_OVERVIEW)
            if subscriptions_page_link:
                subscriptions_page_link.click()
                self.wait_for_element(self.commerce_overview_locators.TXT_OVERVIEW)
                assert self.find_element(self.commerce_overview_locators.TXT_OVERVIEW).text == "Overview", "Overview page is not working as expected"
                assert self.if_element_exists(
                    self.commerce_overview_locators.TXT_ERROR
                ), "could not find 503 error locator={}".format(self.commerce_overview_locators.TXT_ERROR)
                assert self.if_element_exists(
                    self.commerce_overview_locators.TXT_ERROR_MSG
                ), "could not find error msg locator={}".format(self.commerce_overview_locators.TXT_ERROR_MSG)
                assert self.if_element_exists(
                    self.commerce_overview_locators.BTN_BACK_TO_HOME_PAGE
                ), "could not find Back to Vmware cloud services locator={}".format(self.commerce_overview_locators.BTN_BACK_TO_HOME_PAGE)
                
            else:
                mylog.error(
                    "Subscription page could not be located using locator={}".format(
                        self.commerce_locators.NAV_SUBSCRIPTIONS
                    )
                )

        return None
